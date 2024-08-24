
# Understanding a Multi-Container Host Networking Using VxLAN Overlay Network in AWS

This lab demonstrates how to set up container communication between multiple EC2 instances using Virtual Extensible LAN (VxLAN) technology. We'll create a VxLAN overlay network to enable containers on different hosts to communicate as if they were on the same local network.

## What is VxLAN?

VxLAN (Virtual Extensible LAN) is a network virtualization technology that addresses the requirements of Layer 2 and Layer 3 data center network infrastructure in multi-tenant environments. It provides a means to "stretch" a Layer 2 network over an existing Layer 3 infrastructure.

Key features of VxLAN:
- It's a Layer 2 overlay on a Layer 3 network
- Uses a 24-bit segment ID called VNI (VxLAN Network Identifier)
- Supports up to 16 million VxLAN segments in the same administrative domain

## What is VNI?

VNI (VxLAN Network Identifier) is a 24-bit identifier for the LAN segment, similar to a VLAN ID but with a much larger address space. This allows for unique IDs across an entire network, making it suitable for large-scale multi-tenant environments.

## What is VTEP?

VTEP (VxLAN Tunnel End Point) is a component that handles the encapsulation and decapsulation of VxLAN traffic. It has an IP address in the underlay network and is associated with one or more VNIs. VTEPs create stateless tunnels across the network to transport encapsulated frames between source and destination switches.

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-19.png?raw=true)


## Task Overview

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-18.png?raw=true)


### In this hands-on we will do the following:
- Set up two virtual machines (EC2 instances)
- Install Docker on both VMs
- Create a custom Docker network with a specific subnet
- Launch containers with static IP addresses
- Establish a VxLAN bridge using Linux networking features
- Connect the VxLAN bridge to the Docker network
- Test container communication across VMs

By the end of this task, you should have two VMs, each running a Docker container. These containers should be able to communicate with each other over the VxLAN network, despite being on separate physical or virtual hosts.







## Create 2 EC2 instances (VM) in a Public Subnet within AWS VPC using PULUMI

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-15.png?raw=true)

### Configure AWS CLI

Configure AWS CLI with the necessary credentials. Run the following command and follow the prompts to configure it:

```sh
aws configure
```

This command sets up your AWS CLI with the necessary credentials, region, and output format.

![](https://github.com/Konami33/poridhi.io.intern/blob/main/PULUMI/PULUMI%20js/Lab-3/images/5.png?raw=true)

You will find the `AWS Access key` and `AWS Seceret Access key` on Lab description page,where you generated the credentials

![](https://github.com/Konami33/poridhi.io.intern/blob/main/PULUMI/PULUMI%20js/Lab-3/images/6.png?raw=true)


### Set Up a Pulumi Project

1. **Set Up a Pulumi Project**:
- Create a new directory for your project and navigate into it:
    ```sh
    mkdir aws-infra
    cd aws-infra
    ```

2. **Install python `venv`**:

    ```sh 
    sudo apt update
    sudo apt install python3.8-venv
    ```

3. **Initialize a New Pulumi Project**:
- Run the following command to create a new Pulumi project:

    ```sh
    pulumi new aws-python
    ```
    Follow the prompts to set up your project.

4. **Create Key Pair**:

- Create a new key pair for our instances using the following command:

    ```sh
    aws ec2 create-key-pair --key-name my-key  --query 'KeyMaterial' --output text > my-key.pem
    ```

    These commands will create key pair for EC2 instances.

5. **Set File Permissions of the key files**:

- **For Linux**:
    ```sh
    chmod 400 my-key.pem
    ```

### Write Code for infrastructure creation

1. **Open `__main__.py` file in your project directory**:

   ```python
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
   ```

    **NOTE:** Update the security group *inbound rules* accordingly to your requirement. But for now it is set up to allow all traffic from all sources. You can change it later. 

### Deploy the Pulumi Stack

1. **Deploy the stack**:

    ```sh
    pulumi up
    ```
    Review the changes and confirm by typing "yes".

    ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-17.png?raw=true)

### Verify the Deployment

After creating the infra we can see them from the console:

1. `VPC resource map`:

   ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image.png?raw=true)

1. `my-instyance-1`:

    ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-1.png?raw=true)

2. `my-instyance-2`:

    ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-2.png?raw=true)



## SSH into the EC2 instances

Open 2 terminal and go to the folder where you saved the SSH key-pair (`my-key.pem`) file. Use the following command to SSH into the EC2 instances from both the terminal:

```bash
ssh -i "my-key.pem" ubuntu@<EC2-instances-public-IP>
```

Replace `<EC2-instances-public-IP>` with the public IP of your instances. You can get the IP from the AWS console.

## Install Docker and Create a Subnet

On both Hosts/ EC2 instances, follow these steps:

1. **Update the repository and install Docker:**

   ```bash
   sudo apt update
   sudo apt install -y docker.io
   ```

2. **Create a separate Docker bridge network:**

   ```bash
   sudo docker network create --subnet 172.18.0.0/16 vxlan-net
   ```

3. **List all networks in Docker to verify the network creation:**

   ```bash
   sudo docker network ls
   ```

4. **Check the network interfaces on the instance:**

   ```bash
   ip a
   ```

Expected outputs:

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-3.png?raw=true)

**Note:** You have to run these commands in both instances. 


## Run Docker Containers

Let's run docker container `ubuntu` on top of newly created docker bridge network `vxlan-net` and try to ping docker bridge.

### On Host-1 (my-instance-1):

1. **Run an Ubuntu container on the Docker bridge network with a static IP:**

   ```bash
   sudo docker run -d --net vxlan-net --ip 172.18.0.11 ubuntu sleep 3000
   ```

2. **Check that the container is running:**

   ```bash
   sudo docker ps
   ```

    Expected output:

    ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-5.png?raw=true)

3. **Verify the IP address of the container:**

   ```bash
   sudo docker inspect <container_id> | grep IPAddress
   ```

4. **Ping the Docker bridge IP to ensure network connectivity:**

   ```bash
   ping 172.18.0.1 -c 2
   ```

    Expected output:

   ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-6.png?raw=true)

### On Host-2 (my-instance-2):

1. **Run an Ubuntu container on the Docker bridge network with a static IP:**

   ```bash
   sudo docker run -d --net vxlan-net --ip 172.18.0.12 ubuntu sleep 3000
   ```

2. **Check that the container is running:**

   ```bash
   sudo docker ps
   ```

    Expected output:

    ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-7.png?raw=true)

3. **Verify the IP address of the container:**

   ```bash
   sudo docker inspect <container_id> | grep IPAddress
   ```

4. **Ping the Docker bridge IP to ensure network connectivity:**

   ```bash
   ping 172.18.0.1 -c 2
   ```

    Expected output:

   ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-8.png?raw=true)


## Test Container Communication (Pre-VxLAN)

On both hosts, access to the running container and try to ping another hosts running container via IP Address. Though hosts can communicate each other, conatiner communication should fail because there is no tunnel or anything to carry the traffic.

```bash
sudo docker exec -it <container_id> bash

# Inside the container
apt-get update
apt-get install net-tools
apt-get install iputils-ping

# Ping the other container (this should fail)
ping <other_container_ip> -c 2
```

From host-1 container to host-2 container:

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-9.png?raw=true)

From host-2 container to host-1 container:

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-10.png?raw=true)


## Create VxLAN Tunnel

It’s time to create a VxLAN tunnel to establish communication between two hosts running containers. Then attch the vxlan to the docker bridge. Make sure the VNI ID is the same for both hosts.

### Configure VxLAN on Host-01

1. **Check existing network bridges:**

   ```bash
   brctl show
   ```

2. **Create a VxLAN interface on Host-01:**

   ```bash
   sudo ip link add vxlan-demo type vxlan id 100 remote <Host-02_IP> dstport 4789 dev enX0
   ```

   - **`vxlan-demo`**: The name of the VxLAN interface you are creating.
    - **`id 100`**: The VxLAN network identifier (VNI). It should be the same on both hosts.
    - **`remote <Host-01_IP>`**: The private IP address of Host-2 where the remote VxLAN peer is located. Replace `<Host-02_IP>` with the actual IP address of Host-2.
    - **`dstport 4789`**: The UDP port number used for VxLAN communication. The default is 4789.
    - **`dev enX0`**: The network interface on which the VxLAN interface will be created. Here, `enX0` is used, but it should match the primary network interface of the host.

3. **Bring up the VxLAN interface:**

   ```bash
   sudo ip link set vxlan-demo up
   ```

4. **Attach the VxLAN interface to the Docker bridge network:**

   ```bash
   sudo brctl addif <bridge_name> vxlan-demo
   ```

   Replace `<bridge_name>` with the name of the Docker bridge network.(e.g., `br-17218e72c5f9`).

5. **Check the routing table:**

   ```bash
   route -n
   ```

   ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-11.png?raw=true)

### Configure VxLAN on Host-02

1. **Check existing network bridges:**

   ```bash
   brctl show
   ```

2. **Create a VxLAN interface on Host-02:**

   ```bash
   sudo ip link add vxlan-demo type vxlan id 100 remote <Host-01_IP> dstport 4789 dev enX0
   ```
    
    Replace `<Host-01_IP>` with the actual private IP address of Host-1.

3. **Bring up the VxLAN interface:**

   ```bash
   sudo ip link set vxlan-demo up
   ```

4. **Attach the VxLAN interface to the Docker bridge network:**

   ```bash
   sudo brctl addif <bridge_name> vxlan-demo
   ```

   Replace `<bridge_name>` with the name of the Docker bridge network.

5. **Check the routing table:**

   ```bash
   route -n
   ```

   ![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-12.png?raw=true)

## Test Container Communication (Post-VxLAN)

On both hosts, access the running containers and test connectivity. It should work now. A Vxlan Overlay Network Tunnel has been created.

```bash
sudo docker exec -it <container_id> bash

# Ping the other container (this should now succeed)
ping <other_container_ip> -c 2
```

In Host-1:

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-13.png?raw=true)

In host-2:

![alt text](https://github.com/Minhaz00/Multi-Container-Host-Networking/blob/main/images/image-14.png?raw=true)

## Conclusion

In this lab, we created a VxLAN overlay network between two EC2 instances, enabling containers on different hosts to communicate as if they were on the same local network. This illustrates the utility of VxLAN for building scalable and flexible network architectures in multi-tenant environments.

### Key Points:
- **VxLAN Communication**: VxLAN uses UDP port 4789 by default.
- **VNI Consistency**: The VxLAN Network Identifier (VNI) must be identical on both hosts to establish the tunnel.
- **Security Considerations**: In production, use stricter security group rules and implement robust network security practices.

This lab serves as a basic introduction to VxLAN technology and its role in container networking. For more advanced use cases, consider exploring solutions like Docker Swarm or Kubernetes for large-scale container orchestration.

