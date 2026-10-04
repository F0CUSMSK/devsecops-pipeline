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

# resource group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# virtual network
resource "azurerm_virtual_network" "main" {
  name                = "devsecops-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
}

# subnet
resource "azurerm_subnet" "main" {
  name                 = "devsecops-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

# FIX: attach the NSG to the subnet (CKV2_AZURE_31)
resource "azurerm_subnet_network_security_group_association" "main" {
  subnet_id                 = azurerm_subnet.main.id
  network_security_group_id = azurerm_network_security_group.main.id
}

# FIX: identity used by the storage account to read its encryption key (CKV2_AZURE_1)
resource "azurerm_user_assigned_identity" "storage" {
  name                = "devsecops-storage-identity"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
}


resource "azurerm_network_security_group" "main" {
  name                = "devsecops-nsg"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                   = "allow-ssh"
    priority               = 100
    direction              = "Inbound"
    access                 = "Allow"
    protocol               = "Tcp"
    source_port_range      = "*"
    destination_port_range = "22"
    # FIX: restricted to admin IP only, not open to internet
    source_address_prefix      = var.admin_ip
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "deny-all-inbound"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# network interface — no public IP (CKV_AZURE_119)
# the VM is only reachable from inside the VNet / via Azure Bastion
resource "azurerm_network_interface" "main" {
  name                = "devsecops-nic"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.main.id
    private_ip_address_allocation = "Dynamic"
  }
}


resource "azurerm_disk_encryption_set" "main" {
  name                = "devsecops-des"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  key_vault_key_id    = var.key_vault_key_id

  identity {
    type = "SystemAssigned"
  }
}


resource "azurerm_linux_virtual_machine" "main" {
  name                = "devsecops-vm"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  size                = var.vm_size
  admin_username      = var.admin_username

  # FIX: password authentication disabled, SSH key used instead
  disable_password_authentication = true

  # FIX: VM extension operations blocked (CKV_AZURE_50)
  allow_extension_operations = false

  admin_ssh_key {
    username   = var.admin_username
    public_key = var.ssh_public_key
  }

  network_interface_ids = [
    azurerm_network_interface.main.id
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    # FIX: disk encryption enabled
    disk_encryption_set_id = azurerm_disk_encryption_set.main.id
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
}


resource "azurerm_storage_account" "main" {
  name                = "devsecopsstorage"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  account_tier        = "Standard"

  # FIX: geo-redundant replication instead of LRS (CKV_AZURE_206)
  account_replication_type = "GRS"

  # FIX: blob anonymous access disabled (CKV_AZURE_59 / CKV2_AZURE_47)
  allow_nested_items_to_be_public = false

  # FIX: no shared key auth — Entra ID only (CKV2_AZURE_40)
  shared_access_key_enabled = false

  # FIX: private access only — no public network access (CKV_AZURE_190)
  public_network_access_enabled = false

  https_traffic_only_enabled = true

  min_tls_version = "TLS1_2"

  # FIX: queue service logging enabled (CKV_AZURE_33)
  queue_properties {
    logging {
      delete                = true
      read                  = true
      write                 = true
      version               = "1.0"
      retention_policy_days = 7
    }
  }

  # FIX: SAS tokens expire after 1 day (CKV2_AZURE_41)
  sas_policy {
    expiration_action = "Log"
    expiration_period = "1.00:00:00"
  }

  # FIX: blob soft-delete enabled (CKV2_AZURE_38)
  blob_properties {
    delete_retention_policy {
      days = 7
    }
    container_delete_retention_policy {
      days = 7
    }
  }

  # FIX: encrypt storage data with a customer managed key (CKV2_AZURE_1)
  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.storage.id]
  }

  customer_managed_key {
    key_vault_key_id          = var.key_vault_key_id
    user_assigned_identity_id = azurerm_user_assigned_identity.storage.id
  }
}

# FIX: private endpoint for blob access over the VNet only (CKV2_AZURE_33)
resource "azurerm_private_endpoint" "storage" {
  name                = "devsecops-storage-pe"
  location            = var.location
  resource_group_name = azurerm_resource_group.main.name
  subnet_id           = azurerm_subnet.main.id

  private_service_connection {
    name                           = "storage-blob-connection"
    private_connection_resource_id = azurerm_storage_account.main.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }
}
