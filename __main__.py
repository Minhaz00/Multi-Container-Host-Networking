import pulumi
import pulumi_aws as aws


# Create a VPC
vpc = aws.ec2.Vpc("my-vpc",
    cidr_block="10.0.0.0/16",
    tags={
        "Name": "my-vpc",
    })

pulumi.export("vpcId", vpc.id)


# Create a public subnet
public_subnet = aws.ec2.Subnet("my-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.0.0/24",
    availability_zone="ap-southeast-1a",
    map_public_ip_on_launch=True,
    tags={
        "Name": "my-subnet",
    })

pulumi.export("publicSubnetId", public_subnet.id)


# Create an Internet Gateway
igw = aws.ec2.InternetGateway("my-internet-gateway",
    vpc_id=vpc.id,
    tags={
        "Name": "my-internet-gateway",
    })

pulumi.export("igwId", igw.id)


# Create a route table
public_route_table = aws.ec2.RouteTable("my-route-table",
    vpc_id=vpc.id,
    tags={
        "Name": "my-route-table",
    })

pulumi.export("publicRouteTableId", public_route_table.id)


# Create a route in the route table for the Internet Gateway
route = aws.ec2.Route("igw-route",
    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=igw.id)


# Associate the route table with the public subnet
route_table_association = aws.ec2.RouteTableAssociation("public-route-table-association",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id)


# Create a security group for the public instance
public_security_group = aws.ec2.SecurityGroup("public-secgrp",
    vpc_id=vpc.id,
    description="Enable HTTP and SSH access for public instance",
    ingress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ])

# Use the specified Ubuntu 24.04 LTS AMI
ami_id = "ami-01811d4912b4ccb26"


# Create EC2 instances
instance1 = aws.ec2.Instance("my-instance-1",
    instance_type="t2.micro",
    vpc_security_group_ids=[public_security_group.id],
    ami=ami_id,
    subnet_id=public_subnet.id,
    key_name="my-key",
    associate_public_ip_address=True,
    tags={
        "Name": "my-instance-1",
    })

pulumi.export("publicInstanceId", instance1.id)
pulumi.export("publicInstanceIp", instance1.public_ip)


instance2 = aws.ec2.Instance("my-instance-2",
    instance_type="t2.micro",
    vpc_security_group_ids=[public_security_group.id],
    ami=ami_id,
    subnet_id=public_subnet.id,
    key_name="my-key",
    associate_public_ip_address=True,
    tags={
        "Name": "my-instance-2",
    })

pulumi.export("publicInstanceId", instance2.id)
pulumi.export("publicInstanceIp", instance2.public_ip)
