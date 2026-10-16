resource "aws_eks_cluster" "main" {
  name     = "${var.project}-cluster"
  role_arn = aws_iam_role.cluster.arn
  version  = var.kubernetes_version

  vpc_config {
    subnet_ids              = aws_subnet.public[*].id
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  # Lets IAM users and roles be granted Kubernetes access through EKS access
  # entries instead of hand editing the aws-auth ConfigMap. The entry below
  # gives whoever ran terraform admin on the cluster.
  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }

  enabled_cluster_log_types = ["api", "audit"]

  depends_on = [aws_iam_role_policy_attachment.cluster]

  tags = {
    Name = "${var.project}-cluster"
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project}-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = aws_subnet.public[*].id
  instance_types  = [var.node_instance_type]

  scaling_config {
    desired_size = var.node_desired_size
    min_size     = var.node_min_size
    max_size     = var.node_max_size
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [aws_iam_role_policy_attachment.node]

  tags = {
    Name = "${var.project}-nodes"
  }
}

# Addons are pinned to whatever EKS considers default for this Kubernetes
# version, so the cluster comes up with working networking and DNS instead
# of pods stuck in ContainerCreating.
resource "aws_eks_addon" "vpc_cni" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "vpc-cni"
  depends_on   = [aws_eks_node_group.main]
}

resource "aws_eks_addon" "kube_proxy" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "kube-proxy"
  depends_on   = [aws_eks_node_group.main]
}

resource "aws_eks_addon" "coredns" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "coredns"
  depends_on   = [aws_eks_node_group.main]
}

# The HPA reads pod CPU from the metrics server. It is not installed on EKS
# by default, so without this the HPA sits at <unknown> forever.
resource "aws_eks_addon" "metrics_server" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "metrics-server"
  depends_on   = [aws_eks_node_group.main]
}

# Without this nothing can create an EBS volume. EKS ships a gp2
# StorageClass that points at ebs.csi.aws.com, but it does not ship the
# driver behind it, so a PersistentVolumeClaim just sits in Pending with
# "waiting for a volume to be created by the external provisioner". The
# Postgres StatefulSet never starts, and the backend init container then
# fails against a database that was never scheduled.
resource "aws_eks_addon" "ebs_csi" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "aws-ebs-csi-driver"

  # The controller gets its EC2 permissions through IRSA, not from the
  # node role. See the comment in iam.tf for why the node role alone
  # leaves it crash looping.
  service_account_role_arn = aws_iam_role.ebs_csi.arn

  depends_on = [
    aws_eks_node_group.main,
    aws_iam_role_policy_attachment.ebs_csi,
  ]
}
