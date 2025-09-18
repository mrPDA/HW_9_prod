# 🌩️ Упрощенный Kubernetes для демонстрации ML API
# ================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.100"
    }
  }
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = "ru-central1-a"
}

# Service accounts
resource "yandex_iam_service_account" "k8s_sa" {
  name        = "ml-demo-k8s-sa"
  description = "Service account for demo K8s cluster"
}

resource "yandex_iam_service_account" "k8s_nodes_sa" {
  name        = "ml-demo-nodes-sa"
  description = "Service account for demo K8s nodes"
}

# IAM bindings
resource "yandex_resourcemanager_folder_iam_member" "k8s_sa_editor" {
  folder_id = var.yc_folder_id
  role      = "k8s.clusters.agent"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "k8s_sa_vpc_editor" {
  folder_id = var.yc_folder_id
  role      = "vpc.publicAdmin"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_sa.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "k8s_nodes_sa_worker" {
  folder_id = var.yc_folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.k8s_nodes_sa.id}"
}

# Получаем существующую default subnet
data "yandex_vpc_subnet" "default_subnet" {
  name = "default-ru-central1-a"
}

# Kubernetes cluster
resource "yandex_kubernetes_cluster" "demo_cluster" {
  name        = "ml-fraud-detection-demo"
  description = "Demo ML API Kubernetes cluster"
  
  network_id = data.yandex_vpc_subnet.default_subnet.network_id

  master {
    version = "1.32"
    zonal {
      zone      = "ru-central1-a"
      subnet_id = data.yandex_vpc_subnet.default_subnet.id
    }
    public_ip = true
  }

  service_account_id      = yandex_iam_service_account.k8s_sa.id
  node_service_account_id = yandex_iam_service_account.k8s_nodes_sa.id
}

# Node group
resource "yandex_kubernetes_node_group" "demo_nodes" {
  cluster_id  = yandex_kubernetes_cluster.demo_cluster.id
  name        = "ml-demo-workers"
  description = "Demo worker nodes"
  version     = "1.32"

  instance_template {
    platform_id = "standard-v3"

    resources {
      memory = 4
      cores  = 2
    }

    boot_disk {
      type = "network-hdd"
      size = 32
    }

    network_interface {
      nat       = true
      subnet_ids = [data.yandex_vpc_subnet.default_subnet.id]
    }

    container_runtime {
      type = "containerd"
    }
  }

  scale_policy {
    fixed_scale {
      size = 2
    }
  }

  allocation_policy {
    location {
      zone = "ru-central1-a"
    }
  }
}

# Container Registry
resource "yandex_container_registry" "demo_registry" {
  name = "ml-fraud-detection-demo-registry"
}

# Outputs
output "cluster_id" {
  value = yandex_kubernetes_cluster.demo_cluster.id
}

output "cluster_endpoint" {
  value = yandex_kubernetes_cluster.demo_cluster.master[0].external_v4_endpoint
  sensitive = true
}

output "registry_id" {
  value = yandex_container_registry.demo_registry.id
}

output "kubectl_config_command" {
  value = "yc managed-kubernetes cluster get-credentials ${yandex_kubernetes_cluster.demo_cluster.name} --external"
}

output "docker_config_command" {
  value = "yc container registry configure-docker"
}
