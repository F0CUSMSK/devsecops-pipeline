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
