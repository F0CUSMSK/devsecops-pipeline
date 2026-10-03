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

# FIX: admin IP to restrict SSH access — set this to your real IP
variable "admin_ip" {
  description = "Your admin IP address to restrict SSH access"
  default     = "197.0.0.0/24"
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
