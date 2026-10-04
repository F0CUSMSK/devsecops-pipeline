variable "location" {
  description = "Azure region where resources will be created"
  default     = "East US"
}

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  default     = "devsecops-rg"
}

variable "vm_size" {
  description = "Size of the Azure virtual machine"
  default     = "Standard_B1s"
}

variable "admin_username" {
  description = "Admin username for the virtual machine"
  default     = "adminuser"
}

# FIX: SSH is only reachable from inside the VNet (e.g. Azure Bastion),
# so the allowed source must be a private CIDR — the VM has no public IP
variable "admin_ip" {
  description = "Private CIDR allowed to reach the VM over SSH (Bastion / admin subnet)"
  default     = "10.0.0.0/16"
}

# FIX: SSH public key instead of hardcoded password
variable "ssh_public_key" {
  description = "SSH public key for VM authentication"
  sensitive   = true
}

# FIX: Key Vault key ID for disk encryption
variable "key_vault_key_id" {
  description = "Key Vault key ID for disk encryption set"
  sensitive   = true
}
