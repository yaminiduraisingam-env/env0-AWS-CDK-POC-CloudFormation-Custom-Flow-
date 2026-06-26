"""The POC stack: a real, validatable AWS workload.

Creates a VPC (public subnets only, no NAT gateways to keep cost and deploy
time low), an ECS cluster, and an Application Load Balanced Fargate service
running a public nginx image. The ALB exposes a public URL you can curl to
prove the deployment works, then env0 destroy tears the whole stack down.

The resources here exercise the full AWS permission set requested for the POC:
CloudFormation, IAM role creation + iam:PassRole, ECS/Fargate, ECR pulls, VPC
networking, security groups, load balancing, and CloudWatch Logs.
"""
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct


class FargatePocStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Public-subnet-only VPC with no NAT gateways. Fargate tasks get public
        # IPs and pull the container image directly from the public registry.
        # This avoids NAT hourly cost and keeps deploy/destroy fast, which is
        # what we want for a demo lab.
        vpc = ec2.Vpc(
            self,
            "PocVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
        )

        cluster = ecs.Cluster(self, "PocCluster", vpc=vpc)

        # One L3 construct wires up the task definition, execution/task IAM
        # roles, the Fargate service, the ALB, target group, listener, security
        # groups, and a CloudWatch log group.
        service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "PocService",
            cluster=cluster,
            cpu=256,
            memory_limit_mib=512,
            desired_count=1,
            public_load_balancer=True,
            assign_public_ip=True,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(
                    "public.ecr.aws/nginx/nginx:stable"
                ),
                container_port=80,
            ),
        )

        # nginx returns its default page on "/", so a 200-399 health check
        # marks the target healthy quickly.
        service.target_group.configure_health_check(
            path="/",
            healthy_http_codes="200-399",
        )

        CfnOutput(
            self,
            "ServiceURL",
            value=f"http://{service.load_balancer.load_balancer_dns_name}",
            description="Public URL of the Fargate service. Curl this to validate the deploy.",
        )
