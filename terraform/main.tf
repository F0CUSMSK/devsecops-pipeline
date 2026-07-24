
# What this does: Creates a basic Azure setup for my DevSecOps project


terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# first thing i need is a resource group to put everything inside
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# the virtual network for my project
resource "azurerm_virtual_network" "main" {
  name                = "devsecops-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
}

# subnet inside the vnet
resource "azurerm_subnet" "main" {
  name                 = "devsecops-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

# firewall rules for my vm
# BAD PRACTICE: i opened port 22 to everyone, checkov will catch this
resource "azurerm_network_security_group" "main" {
  name                = "devsecops-nsg"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "allow-ssh"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    # this should be my ip only not 0.0.0.0/0
    source_address_prefix      = "0.0.0.0/0"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "allow-http"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    # same problem here, too open
    source_address_prefix      = "0.0.0.0/0"
    destination_address_prefix = "*"
  }
}

# public ip so i can reach my vm
resource "azurerm_public_ip" "main" {
  name                = "devsecops-pip"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
}

# network interface to connect vm to the network
resource "azurerm_network_interface" "main" {
  name                = "devsecops-nic"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}

# my ubuntu vm
# BAD PRACTICE: hardcoded password, gitleaks will find this
# BAD PRACTICE: no disk encryption, tfsec will catch this
resource "azurerm_linux_virtual_machine" "main" {
  name                = "devsecops-vm"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  size                = var.vm_size
  admin_username      = var.admin_username

  # i know this is wrong, the password should come from vault
  # but for now i put it here so gitleaks can detect it
  admin_password                  = "SuperSecret123!"
  disable_password_authentication = false

  network_interface_ids = [
    azurerm_network_interface.main.id
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    # missing encryption here, tfsec will flag this
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
}

# storage account for my project
# BAD PRACTICE: http allowed and weak tls, checkov will catch both
resource "azurerm_storage_account" "main" {
  name                     = "devsecopsstorage"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # should be true but i left it false on purpose
  https_traffic_only_enabled = false 

  # tls 1.0 is outdated and insecure
  min_tls_version = "TLS1_0"
}