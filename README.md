# ansible-role-infosvr-metadata-asset-manager

Ansible role for automating the deployment of metadata using IBM Metadata Asset Manager brokers and bridges.

## Requirements

- Ansible v2.4.x
- 'dsadm'-become-able network access to an IBM Information Server environment

## Role Variables

See `defaults/main.yml` for inline documentation, and the example below for the main variables needed.

Each broker and bridge has its own unique set of parameters.  These are documented in more detail in each of the YAML files under `vars/`, and the bare minimum requirements for all brokers and bridges are documented in `vars/simple_examples.yml`.  Over time the intention is to get all brokers and bridges working, but the list will grow gradually -- expect that only those included in `vars/` for a given version of this role are working.

## Example Playbook

The role is primarily inteded to be imported into other playbooks as-needed for the deployment of metadata -- through any of the supported brokers and bridges in the Information Server environment. (Thus the need for Ansible v2.4.x and the `import_role` module.)

The following example will create an import area, and run the import, for metadata of any files found in `/data/loadable` on the file system of the Information Server engine tier (and record the hostname on which they are found as 'IS-SERVER.IBM.COM').

```
- import_role: name=IBM.infosvr-metadata-asset-manager
  vars:
    ibm_infosvr_metadata_asset_mgr_import_areas:
      - 
        name: Simple_LocalFileConnector_ImportArea
        type: LocalFileConnector
        description: "A simple sample (setting only required fields) for a LocalFileConnector import area"
        metadata_interchange_server: myhost.domain.com
        dcn:
          name: LOCALFS
        assets_to_import:
          - "folder[/data/loadable]"
        hostname: "IS-SERVER.IBM.COM"
```

## License

Apache 2.0

## Author Information

Christopher Grote
