variable "region" {
  description = "AWS region to build in"
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Name prefix for every resource"
  type        = string
  default     = "washq"
}

variable "owner" {
  description = "Tagged on everything so the bill is traceable"
  type        = string
  default     = "amrinder"
}

variable "vpc_cidr" {
  description = "Address range for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "One subnet per availability zone. EKS needs at least two zones."
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]

  validation {
    condition     = length(var.public_subnet_cidrs) >= 2
    error_message = "EKS will not create a cluster with fewer than two subnets in different zones."
  }
}

variable "kubernetes_version" {
  description = "EKS control plane version"
  type        = string
  default     = "1.31"
}

variable "node_instance_type" {
  description = "Worker node size. Must be Free Tier eligible on a Free plan account."
  type        = string
  default     = "m7i-flex.large"

  # t3.medium was the first choice and it fails on an AWS Free plan
  # account. The cluster builds, then the node group sits in CREATE_FAILED
  # with:
  #
  #   AsgInstanceLaunchFailures: The specified instance type is not
  #   eligible for Free Tier
  #
  # The eligible list comes from:
  #   aws ec2 describe-instance-types --region ap-south-1 \
  #     --filters Name=free-tier-eligible,Values=true
  #
  # m7i-flex.large is on it, and at 2 vCPU and 8 GiB it has more room than
  # t3.medium did. On a normal paid account any sensible type works.
}

variable "node_desired_size" {
  description = "Worker nodes to run"
  type        = number
  default     = 2
}

variable "node_min_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  description = "Headroom for the HPA to scale into"
  type        = number
  default     = 4
}
