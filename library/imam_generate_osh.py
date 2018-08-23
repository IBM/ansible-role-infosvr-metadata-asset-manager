#!/usr/bin/python

###
# Copyright 2018 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: imam_generate_osh

short_description: Generates OSH schema files for data files

description:
  - Generates OSH schema files for data files.
  - Based on a SQL (DDL) input of one or more CREATE TABLE statements.

version_added: "2.4"

author:
  - Christopher Grote (@cmgrote)

options:
  ddl:
    description:
      - Name of the SQL file containing the CREATE TABLE statements
    required: true
    type: path
  structure:
    description:
      - Structural definition to use for the OSH schema
      - For example: "file_format='delimited', header='false'"
    required: true
    type: str
  recordfmt:
    description:
      - Formatting to use for the records defined by the OSH schema
      - For example: "delim='|', final_delim=end, null_field='', charset=UTF-8"
    required: true
    type: str
  ext:
    description:
      - Filename extension to expect for the data files
      - For example: "csv"
    required: true
    type: str
  tables:
    description:
      - A list of tables for which to generate an OSH schema
    required: false
    type: list
  dest:
    description:
      - The target directory into which to write the generated OSH schema(s)
    required: true
    type: path
'''

EXAMPLES = '''
- name: generate OSH schema for MY_TABLE
  imam_generate_osh:
    ddl: mydb.sql
    structure: "file_format: 'delimited', header: 'false'"
    recordfmt: "delim='|', final_delim=end, null_field='', charset=UTF-8"
    ext: csv
    tables:
      - MY_TABLE1
      - MY_TABLE2
    dest: /some/location
'''

RETURN = '''
unmapped:
  description: A list of any warnings regarding the OSH schema generation mappings (eg. defaulted types)
  returned: always
  type: list
schemas:
  description: A list of OSH schema files that were created
  returned: always
  type: list
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native
from ansible.module_utils.osh_types import getCreateTableStatementsFromDDL, getColumnDefinitionsFromCreateTableStatement, convertColumnDefinitionToOSHSchemaFieldDefinition
import os
import os.path
import tempfile


def main():

    module_args = dict(
        ddl=dict(type='path', required=True),
        structure=dict(type='str', required=True),
        recordfmt=dict(type='str', required=True),
        ext=dict(type='str', required=True),
        tables=dict(type='list', required=False),
        dest=dict(type='path', required=True),
        unsafe_writes=dict(type='bool', required=False, default=False)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        unmapped=[],
        schemas=[]
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    ddl = module.params['ddl']
    dest = module.params['dest']
    ext = module.params['ext']

    if os.path.isdir(ddl):
        module.fail_json(rc=256, msg='DDL %s is a directory !' % ddl)

    ddl_exists = os.path.exists(ddl)
    if not ddl_exists:
        module.fail_json(rc=257, msg='DDL %s does not exist !' % ddl)

    f = open(to_bytes(ddl), 'rb')
    ddlString = f.read()
    f.close()

    aCreateTbls = getCreateTableStatementsFromDDL(ddlString)
    tablesToFields = {}
    for table in aCreateTbls:
        tblObj = getColumnDefinitionsFromCreateTableStatement(table)
        if module.params['tables']:
            if tblObj['table'] in module.params['tables']:
                tablesToFields[tblObj['table']] = tblObj['columns']
        else:
            tablesToFields[tblObj['table']] = tblObj['columns']

    for tableName in tablesToFields:
        oshSchema = "// FileStructure: " + module.params['structure'] + "\n"
        oshSchema += "record { " + module.params['recordfmt'] + " } ("

        ucaseTblName = tableName.upper()
        if ucaseTblName not in tablesToFields:
            module.fail_json(rc=1, msg='Unable to find table name: %s' % ucaseTblName)

        fieldDefinitions = tablesToFields[ucaseTblName]
        for field in fieldDefinitions:
            colDefn = convertColumnDefinitionToOSHSchemaFieldDefinition(result, field)
            oshSchema += "\n    " + colDefn

        oshSchema += "\n)"

        # Write temporary file with the OSH output,
        # and then move to specified dest location
        try:
            tmpfd, tmpfile = tempfile.mkstemp()
            f = os.fdopen(tmpfd, 'wb')
            f.write(oshSchema)
            f.close()
        except IOError:
            module.fail_json(msg='Unable to create temporary file to output OSH schema', **result)

        # Checksumming to identify change...
        checksum_src = module.sha1(tmpfile)
        checksum_dest = None
        destfile = dest + os.sep + ucaseTblName + ext + ".osh"
        b_dest = to_bytes(destfile, errors='surrogate_or_strict')
        if os.access(b_dest, os.R_OK):
            checksum_dest = module.sha1(destfile)

        # If the file does not already exist and/or checksums are different,
        # move the new file over the old one and mark it as changed; otherwise
        # leave the original file (delete the tmpfile) and that there was no change
        if checksum_src != checksum_dest:
            module.atomic_move(tmpfile,
                            to_native(os.path.realpath(b_dest), errors='surrogate_or_strict'),
                            unsafe_writes=module.params['unsafe_writes'])
            result['schemas'].append(destfile)
            result['changed'] = True
        else:
            result['schemas'].append(destfile)
            os.unlink(tmpfile)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
