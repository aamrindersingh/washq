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
  description = "Worker node size. t3.medium is the smallest that comfortably runs the stack plus Prometheus."
  type        = string
  default     = "t3.medium"
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
