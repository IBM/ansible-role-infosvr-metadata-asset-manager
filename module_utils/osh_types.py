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
"""
This module adds generic utility functions for translating between DDL and OSH data types
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re


sql_type_to_osh_type = {
    "CHAR": "string",
    "DATE": "date",
    "DECIMAL": "decimal",
    "NUMBER": "decimal",
    "INTEGER": "int64",
    "TIME": "time",
    "TIMESTAMP": "timestamp",
    "VARCHAR": "string",
    "NVARCHAR2": "string"
}


def getOSHSchemaTypeForSQLType(result, sqlType):
    # http://www.ibm.com/support/knowledgecenter/en/SSZJPZ_11.5.0/com.ibm.swg.im.iis.ds.parjob.adref.doc/topics/r_deeadvrf_ImportExport_Properties.html
    sqlTypeAlone = sqlType
    sqlTypeLength = ""
    if sqlType.find("(") > 0:
        sqlTypeAlone = sqlType[0:sqlType.find("(")]
        sqlTypeLength = sqlType[(sqlType.find("(") + 1):sqlType.find(")")]
    ucaseSQL = sqlTypeAlone.upper()
    oshSchemaType = "string"
    if ucaseSQL in sql_type_to_osh_type:
        oshSchemaType = sql_type_to_osh_type[ucaseSQL]
        if sqlTypeLength != "":
            if oshSchemaType == "string":
                oshSchemaType += "[max=" + sqlTypeLength + "]"
            else:
                oshSchemaType += "[" + sqlTypeLength + "]"
    else:
        result['warnings'].append("Unsupported SQL data type: " + ucaseSQL)
    return oshSchemaType


def getCreateTableStatementsFromDDL(ddlString):
    tblStatments = []
#    ddlString = fs.readFileSync(ddlFile, 'utf8')
    aLinesDDL = ddlString.split("\n")
    currentTableDef = "";
    idx = 0
    regex = re.compile(r"\s\s+")
    for line in aLinesDDL:
        line = line.strip().upper();
        if line.startswith("CREATE TABLE"):
            if currentTableDef != "":
                tblStatments.append(currentTableDef)
            currentTableDef = regex.sub(string=line, repl=' ')
        elif not line.startswith("--") and line != "":
            currentTableDef += regex.sub(string=line, repl=' ')
        # Also ensure the very last create table statement is included
        if len(aLinesDDL) == (idx + 1) and currentTableDef.startswith("CREATE TABLE"):
            tblStatments.append(currentTableDef)
        idx += 1
    return tblStatments


def getColumnDefinitionsFromCreateTableStatement(ddlCreateTable):
    iDefnStart = ddlCreateTable.find("(")
    iDefnEnd = ddlCreateTable.rfind(")")
    tblName = ddlCreateTable[(len("CREATE TABLE ")):iDefnStart]
    tblName = tblName.replace('"', '').replace("'", "").strip()
    tblDefn = ddlCreateTable[(iDefnStart + 1):iDefnEnd]
    aNaiveColDefns = tblDefn.split(",") # not quite so simple, since DECIMAL(5,2) will be split in the middle...
    aActualColDefns = []
    idx = 0
    while idx < len(aNaiveColDefns):
        candidateCol = aNaiveColDefns[idx]
        if candidateCol.find("(") > 0:
            # If we find an opening (, then greedily consume into the same column until we find the corresponding closing )
            while candidateCol.find(")") < 0:
                idx += 1
                candidateCol += "," + aNaiveColDefns[idx]
        if not candidateCol.startswith("PRIMARY KEY"):
            aActualColDefns.append(candidateCol.replace('"', '').replace('"', ""))
        idx += 1
    return { "table": tblName, "columns": aActualColDefns }


def convertColumnDefinitionToOSHSchemaFieldDefinition(result, ddlCol):
    remainder = ddlCol
    colName = remainder[0:remainder.find(" ")]
    remainder = remainder[len(colName):].strip()
    colType = remainder
    extras = ""
    if remainder.find(" ") > 0:
        colType = remainder[0:remainder.find(" ")]
        extras = remainder[len(colType):].strip()
    if extras == "NOT NULL":
        extras = "not nullable"
    else:
        extras = "nullable"
    return colName + ": " + extras + " " + getOSHSchemaTypeForSQLType(result, colType) + ";";
