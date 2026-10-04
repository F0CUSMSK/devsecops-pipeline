
# FIX: VM has no public IP anymore — expose its private IP instead
output "vm_private_ip" {
  description = "the private ip address of my virtual machine"
  value       = azurerm_network_interface.main.private_ip_address
}


output "vm_name" {
  description = "the name of my virtual machine"
  value       = azurerm_linux_virtual_machine.main.name
}


output "resource_group_name" {
  description = "the resource group where everything lives"
  value       = azurerm_resource_group.main.name
}


output "storage_account_name" {
  description = "the name of my storage account"
  value       = azurerm_storage_account.main.name
}