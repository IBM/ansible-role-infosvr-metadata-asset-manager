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

## Possible variables

### ibm_infosvr_metadata_asset_mgr_import_areas

Use this variable to provide a list (array) of complex structures, each of which defines an import area for Metadata Asset Manager. If the import area does not yet exist, it will be created and then loaded; if an import area by the same name already exists its metadata will be re-imported (the import area will not be replaced).

Example structures, fully documented, can be found under `vars/documented_*.yml`. Simple structures can be found under `vars/simple_examples.yml`.

### ibm_infosvr_metadata_asset_mgr_data_connections

Available only for v11.7+, this variable can be used to define just data connections rather than a complete import area. This is useful if, for example, you want to make use of the automated Discovery capability available from v11.7+ onwards (ie. leveraging the Open Discovery Framework's ability to pipeline the harvesting of metadata, followed by automated column analysis, etc).

### ibm_infosvr_metadata_asset_mgr_odbc_entries

Use this variable to define any ODBC entries that should be added to the `{DSHOME}/.odbc.ini` file. This is often necessary in order to ensure appropriate connectivity, eg. by the ODBC Connector in DataStage and by various server-side connectors in Metadata Asset Manager.

Generally the required keys within each of these objects are:
- `name`: the (unique) name of the ODBC entry
- `type`: the type of ODBC entry, one of `db2`, `dbase`, `informix`, `oracle`, `oraclewire`, `sqlserver`, `sqlservernative`, `sybase`, `sybaseiq`, `salesforce`, `text`, `teradata`, `openedge`, `mysql`, `postgres`, `greenplum`, `hive`, `impala`
- `database`: the name of the database (for RDBMS entries)
- `host`: the hostname or IP address of the system hosting the data source
- `port`: the port number (for RDBMS entries) -- generally this will also be defaulted to the default port for the particular database type

Since each ODBC driver for different platforms supports a variety of platform-specific options, these can also be (optionally) specified. See the templates in `templates/odbc/*.j2` for the options that can be additionally provided; any that are not mandatory (listed above) will be automatically set to their default values in the ODBC configuration if you do not specify other values for them.

## License

Apache 2.0

## Author Information

Christopher Grote
