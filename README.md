# ansible-role-infosvr-metadata-asset-manager

Ansible role for automating the deployment of metadata using IBM Metadata Asset Manager brokers and bridges.

## Requirements

- Ansible v2.4.x
- 'dsadm'-become-able network access to an IBM Information Server environment
- Inventory group names setup the same as `IBM.infosvr` role

## Role Variables

See `defaults/main.yml` for inline documentation, and the example below for the main variables needed.

Each broker and bridge has its own unique set of parameters.  These are documented in more detail in each of the YAML files under `vars/`, and the bare minimum requirements for all brokers and bridges are documented in `vars/simple_examples.yml`.  Over time the intention is to get all brokers and bridges working, but the list will grow gradually -- expect that only those included in `vars/` for a given version of this role are working.

## Example Playbook

The role is primarily inteded to be imported into other playbooks as-needed for the deployment of metadata -- through any of the supported brokers and bridges in the Information Server environment. (Thus the need for Ansible v2.4.x and the `import_role` module.)

The following example will:

1. Add the DB2 drivers included with Information Server to the JDBC configuration.
1. Create a data connection called `AutoJDBC` (if it does not already exist) to connect to a DB2 database called `MYDB` at `myhost.somewhere.com`. (requires Information Server v11.7+)
1. Create an import area, and run the import, for metadata of any files found in `/data/loadable` on the file system of the Information Server engine tier (and record the hostname on which they are found as 'IS-SERVER.IBM.COM').
1. For the `DB2INST1` schema of `MYDB` on the `AutoJDBC` connection, automatically import any metadata (ie. for tables, columns), then run column analysis on these, automatically-detect term assignments, run data quality analysis, and once completed publish any results to Information Governance Catalog. (requires Information Server v11.7+)

Note tha the order in which the variables are defined does not matter -- the role automatically takes care of running them in the appropriate order such that dependent objects are run first (eg. JDBC configuration is completed before attempting to do any data connectivity via data connections or import areas).

```yml
- import_role: name=IBM.infosvr-metadata-asset-manager
  vars:
    ibm_infosvr_metadata_asset_mgr_import_areas:
      - name: Simple_LocalFileConnector_ImportArea
        type: LocalFileConnector
        description: "A simple sample (setting only required fields) for a LocalFileConnector import area"
        metadata_interchange_server: myhost.domain.com
        dcn:
          name: LOCALFS
        assets_to_import:
          - "folder[/data/loadable]"
        hostname: "IS-SERVER.IBM.COM"
    ibm_infosvr_metadata_asset_mgr_jdbc_entries:
      classpaths:
        - /opt/IBM/InformationServer/ASBNode/lib/java/db2jcc.jar
      classnames:
        - com.ibm.db2.jcc.DB2Driver
    ibm_infosvr_metadata_asset_mgr_data_connections:
      - name: AutoJDBC
        type: JDBCConnector
        description: Data connection for automatically discovering against a JDBC source
        url: jdbc:db2://myhost.somewhere.com:50000/MYDB
        username: db2inst1
        password: "{{ a_password_from_eg_vault }}"
    ibm_infosvr_metadata_asset_mgr_discover_sources:
      - dcn: AutoJDBC
        project: UGDefaultWorkspace
        target_host: myhost.somewhere.com
        steps:
          - import
          - columnAnalysis
          - termAssignment
          - dataQualityAnalysis
          - publish
        parameters:
          rootAssets: schema[MYDB|DB2INST1]
          Asset_description_already_exists: Replace_existing_description
```

## Possible variables

### ibm_infosvr_metadata_asset_mgr_import_areas

Use this variable to provide a list (array) of complex structures, each of which defines an import area for Metadata Asset Manager. If the import area does not yet exist, it will be created and then loaded; if an import area by the same name already exists its metadata will be re-imported (the import area will not be replaced).

Example structures, fully documented, can be found under `vars/documented_*.yml`. Simple structures can be found under `vars/simple_examples.yml`.

### ibm_infosvr_metadata_asset_mgr_data_connections

Available only for v11.7+, this variable can be used to define just data connections rather than a complete import area. This is useful if, for example, you want to make use of the automated Discovery capability available from v11.7+ onwards (ie. leveraging the Open Discovery Framework's ability to pipeline the harvesting of metadata, followed by automated column analysis, etc).

### ibm_infosvr_metadata_asset_mgr_odbc_entries

Use this variable to define any ODBC entries that should be added to the `{DSHOME}/.odbc.ini` file. This is necessary in order to ensure appropriate connectivity via ODBC, eg. by the ODBC connections in DataStage and IMAM.

Generally the required keys within each of these objects are:
- `name`: the (unique) name of the ODBC entry
- `description`: a description of the ODBC entry (should not use the character `=` anywhere)
- `type`: the type of ODBC entry, one of `db2`, `dbase`, `informix`, `oracle`, `oraclewire`, `sqlserver`, `sqlservernative`, `sybase`, `sybaseiq`, `salesforce`, `text`, `teradata`, `openedge`, `mysql`, `postgres`, `greenplum`, `hive`, `impala`
- `database`: the name of the database (for RDBMS entries)
- `host`: the hostname or IP address of the system hosting the data source
- `port`: the port number (for RDBMS entries) -- generally this will also be defaulted to the default port for the particular database type

Since each ODBC driver for different platforms supports a variety of platform-specific options, these can also be (optionally) specified. See the templates in `templates/odbc/*.j2` for the options that can be additionally provided; any that are not mandatory (listed above) will be automatically set to their default values in the ODBC configuration if you do not specify other values for them.

Finally, if you are aware of additional properties that you want to add to a particular entry, which have no default values (ie. are not already listed in the template mentioned above), add them to an `extras` entry as key-value pairs.

**Examples**:

```yml
ibm_infosvr_metadata_asset_mgr_odbc_entries:
  - name: IADB on DB2
    description: Connection to IADB on DB2
    type: db2
    database: IADB
    host: infosvr.vagrant.ibm.com
  - name: Test database on Oracle
    description: Connection to some test data set on Oracle
    type: oracle
    database: TESTDB
    host: infosvr.vagrant.ibm.com
    SID: TESTDB
    extras:
      - QueryTimeout: -1
      - ColumnSizeAsCharacter: 1
      - ColumnsAsChar: 1
```

### ibm_infosvr_metadata_asset_mgr_jdbc_entries

Use this variable to define any JDBC classes that should be included in the `{DSHOME}/isjdbc.config` file. This is necessary in order to ensure appropriate connectivity via JDBC, eg. by the JDBC connections in DataStage and IMAM.

There are two sub-keys required:
- `classpaths`: defines the locations of any Java classes that should be added to the CLASSPATH, ie. which provide JDBC drivers
- `classnames`: defines the names of the Java classes that provide the JDBC drivers within the classpaths above

The role will ensure that any classpaths or classnames not already included in the configuration file are added to it, and will leave any that are already present.

**Examples**:

```yml
ibm_infosvr_metadata_asset_mgr_jdbc_entries:
  classpaths:
    - "{{ ibm_infosvr_metadata_asset_mgr_install_location }}/ASBNode/lib/java/db2jcc.jar"
  classnames:
    - com.ibm.db2.jcc.DB2Driver
```

### ibm_infosvr_metadata_asset_mgr_osh_schemas

Use this variable to define any DDL files (containing CREATE TABLE statements) that should be used to generate OSH schema files for data files that would capture the same content as the database tables.

All parameters are required, except for the `tables` parameter -- if not specified, an OSH schema will be generated for every CREATE TABLE statement found in the specified `ddl`.

This will create the following:
- one (blank) data file under the specified `dest` directory for each CREATE TABLE statement in the specified `ddl` (limited by the tables defined in the optional `tables` parameter), using the specified `fileext` as the file extension
- one OSH schema file under the same specified `dest` directory for each of the blank data files created, appending `.osh` as an additional file extension

**Examples**:

```yml
ibm_infosvr_metadata_asset_mgr_osh_schemas:
  - ddl: /some/location/MYDB.sql
    structure: "file_format: 'delimited', header: 'false'"
    recordfmt: "delim='|', final_delim=end, null_field='', charset=UTF-8"
    dest: /some/target/directory
    fileext: csv
    tables:
      - TABLE1
      - TABLE2
```

The example above will create:
- `/some/target/directory/TABLE1.csv`
- `/some/target/directory/TABLE1.csv.osh`
- `/some/target/directory/TABLE2.csv`
- `/some/target/directory/TABLE2.csv.osh`

### ibm_infosvr_metadata_asset_mgr_discover_sources

Use this variable to define any data sources that should be automatically discovered using the Open Discovery Framework in v11.7+

The following sub-keys are required for each entry:

- `dcn`: specifies the name of the data connection to use for discovery
- `project`: specifies the name of the Information Analyzer project in which to do the discovery
- `target_host`: specifies the hostname that should be used for the source that is being discovered

The remainder of the sub-keys are optional:

- `parameters`: provides a set of sub-keys defining additional behaviour or restrictions to apply to the discovery, eg:
  - `rootAssets`: defines the subset of assets for which to run discovery (without which _all_ assets on the target will be discovered -- eg. all files in all directories, all tables across all schemas)
  - `Asset_description_already_exists`: defines how to handle the situation where a particular technical asset with the same identity already exists
  - other parameters are also possible depending on the type of source -- see the Information Server Knowledge Centre for more details
- `steps`: indicates which steps of the discovery process should be applied, and can include:
  - `import`: discovers and ingests the technical metadata for the source to the Information Governance Catalog
  - `columnAnalysis`: runs column analysis agains the source, determining formats, frequency distributions of values, and detecting data classes (dependent on the `import` being done)
  - `termAssignment`: attempts to automatically detect business terms to assign to the technical metadata based on their detected data classes, column names, and previous relationships from which the system has learned (if configured) (dependent on the `columnAnalysis` being done), including applying any Automation Rules that automatically assign data rules based on the assigned terms
  - `dataQualityAnalysis`: runs through a set of standard quality checks, eg. looking for outlier values, and any data rules that have been automatically assigned
  - `publish`: publishes the results of all of the other steps to the Information Governance Catalog

Note that up until the last `publish` step, all work has been kept in an unpublished state in the Information Analyzer project / workspace. Once published, all of the various analyses are visible by anyone in the Information Governance Catalog. You may therefore wish to leave off this last `publish` step in order to force a review (and manual decision to publish) within Information Analyzer. (By default, if the steps are not specified, the discovery will include all steps _except_ the `publish` step.)

Also be aware that the `schema[DBNAME|SCHEMA]` format of the `rootAssets`, when applied to JDBC connections, may require special values for the `DBNAME` portion (eg. for DB2, since the database is inherent in the URL provided as part of the data connection, you always provide `db2` as the `DBNAME` here, rather than the actual database name).

**Examples**:

```yml
ibm_infosvr_metadata_asset_mgr_discover_sources:
  - dcn: AutoJDBC
    project: UGDefaultWorkspace
    target_host: myhost.somewhere.com
    steps:
      - import
      - columnAnalysis
      - termAssignment
      - dataQualityAnalysis
      - publish
    parameters:
      rootAssets: schema[MYDB|DB2INST1]
      Asset_description_already_exists: Replace_existing_description
```

## License

Apache 2.0

## Author Information

Christopher Grote
