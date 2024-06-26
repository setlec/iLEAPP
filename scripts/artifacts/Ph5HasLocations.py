# Photos.sqlite
# Author:  Scott Koenig, assisted by past contributors
# Version: 1.3
#
#   Description:
#   Parses basic asset record data from Photos.sqlite for assets that have valid locations and supports iOS 11-17.
#   The results for this script will contain one record per ZASSET table Z_PK value.
#   This parser is based on research and SQLite queries written by Scott Koenig
#   https://theforensicscooter.com/ and queries found at https://github.com/ScottKjr3347
#

import os
from datetime import datetime
import pytz
import json
import shutil
import base64
from PIL import Image
from pillow_heif import register_heif_opener
import glob
import sys
import stat
from pathlib import Path
import sqlite3
import plistlib
import nska_deserialize as nd
import scripts.artifacts.artGlobals
from packaging import version
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, kmlgen, is_platform_windows, media_to_html, open_sqlite_db_readonly


def get_ph5haslocationsphdapsql(files_found, report_folder, seeker, wrap_text, timezone_offset):
    for file_found in files_found:
        file_found = str(file_found)
        
        if file_found.endswith('.sqlite'):
            break
      
    if report_folder.endswith('/') or report_folder.endswith('\\'):
        report_folder = report_folder[:-1]
    iosversion = scripts.artifacts.artGlobals.versionf
    if version.parse(iosversion) <= version.parse("10.3.4"):
        logfunc("Unsupported version for PhotosData-Photos.sqlite assets with valid locations from iOS " + iosversion)
    if (version.parse(iosversion) >= version.parse("11")) & (version.parse(iosversion) < version.parse("13")):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZGENERICASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
        WHERE zAsset.ZLATITUDE > 0
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13]))

                counter += 1

            description = 'Parses basic asset record data from PhotoData-Photos.sqlite for assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 11-13. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Other_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.1-Has Locations-PhDaPsql', description)
            report.add_script()
            data_headers = ('zAsset-Date Created',
                            'zAsset-Latitude',
                            'zAsset-Longitude',
                            'zAsset-Directory-Path',
                            'zAsset-Filename',
                            'zAddAssetAttr- Original Filename',
                            'zCldMast- Original Filename',
                            'zCldMast-Import Session ID- AirDrop-StillTesting',
                            'zAddAssetAttr-Shifted Location Data-8',
                            'zAddAssetAttr-Reverse Location Data-9',
                            'zAsset-zPK',
                            'zAddAssetAttr-zPK',
                            'zAsset-UUID = store.cloudphotodb',
                            'zAddAssetAttr-Master Fingerprint')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.1-Has Locations-PhDaPsql'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.1-Has Locations-PhDaPsql'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for PhotoData-Photos.sqlite assets with valid locations')

        db.close()
        return

    elif (version.parse(iosversion) >= version.parse("13")) & (version.parse(iosversion) < version.parse("14")):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        CASE zAddAssetAttr.ZSHIFTEDLOCATIONISVALID
            WHEN 0 THEN '0-Shifted Location Not Valid-0'
            WHEN 1 THEN '1-Shifted Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZSHIFTEDLOCATIONISVALID || ''
        END AS 'zAddAssetAttr-Shifted Location Valid',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE zAddAssetAttr.ZREVERSELOCATIONDATAISVALID
            WHEN 0 THEN '0-Reverse Location Not Valid-0'
            WHEN 1 THEN '1-Reverse Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZREVERSELOCATIONDATAISVALID || ''
        END AS 'zAddAssetAttr-Reverse Location Is Valid',		
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        CASE AAAzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Cloud-1'
            WHEN 2 THEN '2-StillTesting-This Device-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || AAAzCldMastMedData.Z_OPT || ''
        END AS 'AAAzCldMastMedData-zOPT',
        zAddAssetAttr.ZMEDIAMETADATATYPE AS 'zAddAssetAttr-Media Metadata Type',
        CASE
            WHEN AAAzCldMastMedData.ZDATA > 0 THEN 'AAAzCldMastMedData-Data_has_Plist'
            ELSE 'AAAzCldMastMedData-Data_Empty-NULL'
        END AS 'AAAzCldMastMedData-Data',
        CASE CMzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Has_CldMastAsset-1'
            WHEN 2 THEN '2-StillTesting-Local_Asset-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || CMzCldMastMedData.Z_OPT || ''
        END AS 'CldMasterzCldMastMedData-zOPT',
        zCldMast.ZMEDIAMETADATATYPE AS 'zCldMast-Media Metadata Type',		
        CASE
            WHEN CMzCldMastMedData.ZDATA > 0 THEN 'CMzCldMastMedData-Data_has_Plist'
            ELSE 'CMzCldMastMedData-Data_Empty-NULL'
        END AS 'CMzCldMastMedData-Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZGENERICASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA AAAzCldMastMedData ON
             AAAzCldMastMedData.Z_PK = zAddAssetAttr.ZMEDIAMETADATA
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA CMzCldMastMedData ON
             CMzCldMastMedData.Z_PK = zCldMast.ZMEDIAMETADATA
        WHERE zAsset.ZLATITUDE > 0
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18],
                                row[19], row[20], row[21]))

                counter += 1

            description = 'Parses basic asset record data from PhotoData-Photos.sqlite for assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 11-13. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Other_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.1-Has Locations-PhDaPsql', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zAsset-Longitude-2',
                            'zAsset-Directory-Path-3',
                            'zAsset-Filename-4',
                            'zAddAssetAttr- Original Filename-5',
                            'zCldMast- Original Filename-6',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-7',
                            'zAddAssetAttr-Shifted Location Valid-8',
                            'zAddAssetAttr-Shifted Location Data-9',
                            'zAddAssetAttr-Reverse Location Is Valid-10',
                            'zAddAssetAttr-Reverse Location Data-11',
                            'AAAzCldMastMedData-zOPT-12',
                            'zAddAssetAttr-Media Metadata Type-13',
                            'AAAzCldMastMedData-Data-14',
                            'CldMasterzCldMastMedData-zOPT-15',
                            'zCldMast-Media Metadata Type-16',
                            'CMzCldMastMedData-Data-17',
                            'zAsset-zPK-18',
                            'zAddAssetAttr-zPK-19',
                            'zAsset-UUID = store.cloudphotodb-20',
                            'zAddAssetAttr-Master Fingerprint-21')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.1-Has Locations-PhDaPsql'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.1-Has Locations-PhDaPsql'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for PhotoData-Photos.sqlite assets with valid locations')

        db.close()
        return

    elif (version.parse(iosversion) >= version.parse("14")) & (version.parse(iosversion) < version.parse("15")):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT 
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        zExtAttr.ZLATITUDE AS 'zExtAttr-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zExtAttr.ZLONGITUDE AS 'zExtAttr-Longitude',
        CASE zAddAssetAttr.ZGPSHORIZONTALACCURACY
            WHEN -1.0 THEN '-1.0'
            ELSE zAddAssetAttr.ZGPSHORIZONTALACCURACY
        END AS 'zAddAssetAttr-GPS Horizontal Accuracy',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        CASE zAddAssetAttr.ZSHIFTEDLOCATIONISVALID
            WHEN 0 THEN '0-Shifted Location Not Valid-0'
            WHEN 1 THEN '1-Shifted Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZSHIFTEDLOCATIONISVALID || ''
        END AS 'zAddAssetAttr-Shifted Location Valid',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE zAddAssetAttr.ZREVERSELOCATIONDATAISVALID
            WHEN 0 THEN '0-Reverse Location Not Valid-0'
            WHEN 1 THEN '1-Reverse Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZREVERSELOCATIONDATAISVALID || ''
        END AS 'zAddAssetAttr-Reverse Location Is Valid',		
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        CASE AAAzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Cloud-1'
            WHEN 2 THEN '2-StillTesting-This Device-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || AAAzCldMastMedData.Z_OPT || ''
        END AS 'AAAzCldMastMedData-zOPT',
        zAddAssetAttr.ZMEDIAMETADATATYPE AS 'zAddAssetAttr-Media Metadata Type',
        CASE
            WHEN AAAzCldMastMedData.ZDATA > 0 THEN 'AAAzCldMastMedData-Data_has_Plist'
            ELSE 'AAAzCldMastMedData-Data_Empty-NULL'
        END AS 'AAAzCldMastMedData-Data',
        CASE CMzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Has_CldMastAsset-1'
            WHEN 2 THEN '2-StillTesting-Local_Asset-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || CMzCldMastMedData.Z_OPT || ''
        END AS 'CldMasterzCldMastMedData-zOPT',
        zCldMast.ZMEDIAMETADATATYPE AS 'zCldMast-Media Metadata Type',		
        CASE
            WHEN CMzCldMastMedData.ZDATA > 0 THEN 'CMzCldMastMedData-Data_has_Plist'
            ELSE 'CMzCldMastMedData-Data_Empty-NULL'
        END AS 'CMzCldMastMedData-Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZEXTENDEDATTRIBUTES zExtAttr ON zExtAttr.Z_PK = zAsset.ZEXTENDEDATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA AAAzCldMastMedData ON
             AAAzCldMastMedData.Z_PK = zAddAssetAttr.ZMEDIAMETADATA
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA CMzCldMastMedData ON
             CMzCldMastMedData.Z_PK = zCldMast.ZMEDIAMETADATA
        WHERE (zAsset.ZLATITUDE > 0) OR
          (zExtAttr.ZLATITUDE > 0)
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18],
                                row[19], row[20], row[21], row[22], row[23], row[24]))

                counter += 1

            description = 'Parses basic asset record data from PhotoData-Photos.sqlite for assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 14. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Other_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.1-Has Locations-PhDaPsql', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zExtAttr-Latitude-2',
                            'zAsset-Longitude-3',
                            'zExtAttr-Longitude-4',
                            'zAddAssetAttr-GPS Horizontal Accuracy-5',
                            'zAsset-Directory-Path-6',
                            'zAsset-Filename-7',
                            'zAddAssetAttr- Original Filename-8',
                            'zCldMast- Original Filename-9',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-10',
                            'zAddAssetAttr-Shifted Location Valid-11',
                            'zAddAssetAttr-Shifted Location Data-12',
                            'zAddAssetAttr-Reverse Location Is Valid-13',
                            'zAddAssetAttr-Reverse Location Data-14',
                            'AAAzCldMastMedData-zOPT-15',
                            'zAddAssetAttr-Media Metadata Type-16',
                            'AAAzCldMastMedData-Data-17',
                            'CldMasterzCldMastMedData-zOPT-18',
                            'zCldMast-Media Metadata Type-19',
                            'CMzCldMastMedData-Data-20',
                            'zAsset-zPK-21',
                            'zAddAssetAttr-zPK-22',
                            'zAsset-UUID = store.cloudphotodb-23',
                            'zAddAssetAttr-Master Fingerprint-24')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.1-Has Locations-PhDaPsql'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.1-Has Locations-PhDaPsql'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for PhotoData-Photos.sqlite assets with valid locations')

        db.close()
        return

    elif version.parse(iosversion) >= version.parse("15"):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        zExtAttr.ZLATITUDE AS 'zExtAttr-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zExtAttr.ZLONGITUDE AS 'zExtAttr-Longitude',
        CASE zAddAssetAttr.ZGPSHORIZONTALACCURACY
            WHEN -1.0 THEN '-1.0'
            ELSE zAddAssetAttr.ZGPSHORIZONTALACCURACY
        END AS 'zAddAssetAttr-GPS Horizontal Accuracy',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        zAddAssetAttr.ZSYNDICATIONIDENTIFIER AS 'zAddAssetAttr- Syndication Identifier-SWY-Files',
        CASE zAddAssetAttr.ZSHIFTEDLOCATIONISVALID
            WHEN 0 THEN '0-Shifted Location Not Valid-0'
            WHEN 1 THEN '1-Shifted Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZSHIFTEDLOCATIONISVALID || ''
        END AS 'zAddAssetAttr-Shifted Location Valid',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE zAddAssetAttr.ZREVERSELOCATIONDATAISVALID
            WHEN 0 THEN '0-Reverse Location Not Valid-0'
            WHEN 1 THEN '1-Reverse Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZREVERSELOCATIONDATAISVALID || ''
        END AS 'zAddAssetAttr-Reverse Location Is Valid',		
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        CASE AAAzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Cloud-1'
            WHEN 2 THEN '2-StillTesting-This Device-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || AAAzCldMastMedData.Z_OPT || ''
        END AS 'AAAzCldMastMedData-zOPT',
        zAddAssetAttr.ZMEDIAMETADATATYPE AS 'zAddAssetAttr-Media Metadata Type',
        CASE
            WHEN AAAzCldMastMedData.ZDATA > 0 THEN 'AAAzCldMastMedData-Data_has_Plist'
            ELSE 'AAAzCldMastMedData-Data_Empty-NULL'
        END AS 'AAAzCldMastMedData-Data',
        CASE CMzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Has_CldMastAsset-1'
            WHEN 2 THEN '2-StillTesting-Local_Asset-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || CMzCldMastMedData.Z_OPT || ''
        END AS 'CldMasterzCldMastMedData-zOPT',
        zCldMast.ZMEDIAMETADATATYPE AS 'zCldMast-Media Metadata Type',		
        CASE
            WHEN CMzCldMastMedData.ZDATA > 0 THEN 'CMzCldMastMedData-Data_has_Plist'
            ELSE 'CMzCldMastMedData-Data_Empty-NULL'
        END AS 'CMzCldMastMedData-Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZEXTENDEDATTRIBUTES zExtAttr ON zExtAttr.Z_PK = zAsset.ZEXTENDEDATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA AAAzCldMastMedData ON
             AAAzCldMastMedData.Z_PK = zAddAssetAttr.ZMEDIAMETADATA
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA CMzCldMastMedData ON
             CMzCldMastMedData.Z_PK = zCldMast.ZMEDIAMETADATA
        WHERE (zAsset.ZLATITUDE > 0) OR
          (zExtAttr.ZLATITUDE > 0)
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18],
                                row[19], row[20], row[21], row[22], row[23], row[24], row[25]))

                counter += 1

            description = 'Parses basic asset record data from PhotoData-Photos.sqlite for assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 15-17. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Other_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.1-Has Locations-PhDaPsql', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zExtAttr-Latitude-2',
                            'zAsset-Longitude-3',
                            'zExtAttr-Longitude-4',
                            'zAddAssetAttr-GPS Horizontal Accuracy-5',
                            'zAsset-Directory-Path-6',
                            'zAsset-Filename-7',
                            'zAddAssetAttr- Original Filename-8',
                            'zCldMast- Original Filename-9',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-10',
                            'zAddAssetAttr- Syndication Identifier-SWY-Files-11',
                            'zAddAssetAttr-Shifted Location Valid-12',
                            'zAddAssetAttr-Shifted Location Data-13',
                            'zAddAssetAttr-Reverse Location Is Valid-14',
                            'zAddAssetAttr-Reverse Location Data-15',
                            'AAAzCldMastMedData-zOPT-16',
                            'zAddAssetAttr-Media Metadata Type-17',
                            'AAAzCldMastMedData-Data-18',
                            'CldMasterzCldMastMedData-zOPT-19',
                            'zCldMast-Media Metadata Type-20',
                            'CMzCldMastMedData-Data-21',
                            'zAsset-zPK-22',
                            'zAddAssetAttr-zPK-23',
                            'zAsset-UUID = store.cloudphotodb-24',
                            'zAddAssetAttr-Master Fingerprint-25')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.1-Has Locations-PhDaPsql'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.1-Has Locations-PhDaPsql'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for PhotoData-Photos.sqlite assets with valid locations')

        db.close()
        return


def get_ph5haslocationssyndpl(files_found, report_folder, seeker, wrap_text, timezone_offset):
    for file_found in files_found:
        file_found = str(file_found)

        if file_found.endswith('.sqlite'):
            break

    if report_folder.endswith('/') or report_folder.endswith('\\'):
        report_folder = report_folder[:-1]
    iosversion = scripts.artifacts.artGlobals.versionf
    if version.parse(iosversion) <= version.parse("10.3.4"):
        logfunc("Unsupported version for Syndication.photoslibrary-database-Photos.sqlite assets with valid locations iOS " + iosversion)
    if (version.parse(iosversion) >= version.parse("11")) & (version.parse(iosversion) < version.parse("13")):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZGENERICASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
        WHERE zAsset.ZLATITUDE > 0
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13]))

                counter += 1

            description = 'Parses basic asset record data from Syndication.photoslibrary-Photos.sqlite for' \
                          ' assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 11-13. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Syndication_PL_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.2-Has Locations-SyndPL', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zAsset-Longitude-2',
                            'zAsset-Directory-Path-3',
                            'zAsset-Filename-4',
                            'zAddAssetAttr- Original Filename-5',
                            'zCldMast- Original Filename-6',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-7',
                            'zAddAssetAttr-Shifted Location Data-8',
                            'zAddAssetAttr-Reverse Location Data-9',
                            'zAsset-zPK-10',
                            'zAddAssetAttr-zPK-11',
                            'zAsset-UUID = store.cloudphotodb-12',
                            'zAddAssetAttr-Master Fingerprint-13')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.2-Has Locations-SyndPL'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.2-Has Locations-SyndPL'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for Syndication.photoslibrary-Photos.sqlite assets with valid locations')

        db.close()
        return

    elif (version.parse(iosversion) >= version.parse("13")) & (version.parse(iosversion) < version.parse("14")):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        CASE zAddAssetAttr.ZSHIFTEDLOCATIONISVALID
            WHEN 0 THEN '0-Shifted Location Not Valid-0'
            WHEN 1 THEN '1-Shifted Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZSHIFTEDLOCATIONISVALID || ''
        END AS 'zAddAssetAttr-Shifted Location Valid',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE zAddAssetAttr.ZREVERSELOCATIONDATAISVALID
            WHEN 0 THEN '0-Reverse Location Not Valid-0'
            WHEN 1 THEN '1-Reverse Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZREVERSELOCATIONDATAISVALID || ''
        END AS 'zAddAssetAttr-Reverse Location Is Valid',		
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        CASE AAAzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Cloud-1'
            WHEN 2 THEN '2-StillTesting-This Device-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || AAAzCldMastMedData.Z_OPT || ''
        END AS 'AAAzCldMastMedData-zOPT',
        zAddAssetAttr.ZMEDIAMETADATATYPE AS 'zAddAssetAttr-Media Metadata Type',
        CASE
            WHEN AAAzCldMastMedData.ZDATA > 0 THEN 'AAAzCldMastMedData-Data_has_Plist'
            ELSE 'AAAzCldMastMedData-Data_Empty-NULL'
        END AS 'AAAzCldMastMedData-Data',
        CASE CMzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Has_CldMastAsset-1'
            WHEN 2 THEN '2-StillTesting-Local_Asset-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || CMzCldMastMedData.Z_OPT || ''
        END AS 'CldMasterzCldMastMedData-zOPT',
        zCldMast.ZMEDIAMETADATATYPE AS 'zCldMast-Media Metadata Type',		
        CASE
            WHEN CMzCldMastMedData.ZDATA > 0 THEN 'CMzCldMastMedData-Data_has_Plist'
            ELSE 'CMzCldMastMedData-Data_Empty-NULL'
        END AS 'CMzCldMastMedData-Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZGENERICASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA AAAzCldMastMedData ON
             AAAzCldMastMedData.Z_PK = zAddAssetAttr.ZMEDIAMETADATA
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA CMzCldMastMedData ON
             CMzCldMastMedData.Z_PK = zCldMast.ZMEDIAMETADATA
        WHERE zAsset.ZLATITUDE > 0
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18],
                                row[19], row[20], row[21]))

                counter += 1

            description = 'Parses basic asset record data from Syndication.photoslibrary-Photos.sqlite for' \
                          ' assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 11-13. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Syndication_PL_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.2-Has Locations-SyndPL', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zAsset-Longitude-2',
                            'zAsset-Directory-Path-3',
                            'zAsset-Filename-4',
                            'zAddAssetAttr- Original Filename-5',
                            'zCldMast- Original Filename-6',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-7',
                            'zAddAssetAttr-Shifted Location Valid-8',
                            'zAddAssetAttr-Shifted Location Data-9',
                            'zAddAssetAttr-Reverse Location Is Valid-10',
                            'zAddAssetAttr-Reverse Location Data-11',
                            'AAAzCldMastMedData-zOPT-12',
                            'zAddAssetAttr-Media Metadata Type-13',
                            'AAAzCldMastMedData-Data-14',
                            'CldMasterzCldMastMedData-zOPT-15',
                            'zCldMast-Media Metadata Type-16',
                            'CMzCldMastMedData-Data-17',
                            'zAsset-zPK-18',
                            'zAddAssetAttr-zPK-19',
                            'zAsset-UUID = store.cloudphotodb-20',
                            'zAddAssetAttr-Master Fingerprint-21')

            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.2-Has Locations-SyndPL'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.2-Has Locations-SyndPL'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for Syndication.photoslibrary-Photos.sqlite assets with valid locations')

        db.close()
        return

    elif (version.parse(iosversion) >= version.parse("14")) & (version.parse(iosversion) < version.parse("15")):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT 
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        zExtAttr.ZLATITUDE AS 'zExtAttr-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zExtAttr.ZLONGITUDE AS 'zExtAttr-Longitude',
        CASE zAddAssetAttr.ZGPSHORIZONTALACCURACY
            WHEN -1.0 THEN '-1.0'
            ELSE zAddAssetAttr.ZGPSHORIZONTALACCURACY
        END AS 'zAddAssetAttr-GPS Horizontal Accuracy',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        CASE zAddAssetAttr.ZSHIFTEDLOCATIONISVALID
            WHEN 0 THEN '0-Shifted Location Not Valid-0'
            WHEN 1 THEN '1-Shifted Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZSHIFTEDLOCATIONISVALID || ''
        END AS 'zAddAssetAttr-Shifted Location Valid',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE zAddAssetAttr.ZREVERSELOCATIONDATAISVALID
            WHEN 0 THEN '0-Reverse Location Not Valid-0'
            WHEN 1 THEN '1-Reverse Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZREVERSELOCATIONDATAISVALID || ''
        END AS 'zAddAssetAttr-Reverse Location Is Valid',		
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        CASE AAAzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Cloud-1'
            WHEN 2 THEN '2-StillTesting-This Device-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || AAAzCldMastMedData.Z_OPT || ''
        END AS 'AAAzCldMastMedData-zOPT',
        zAddAssetAttr.ZMEDIAMETADATATYPE AS 'zAddAssetAttr-Media Metadata Type',
        CASE
            WHEN AAAzCldMastMedData.ZDATA > 0 THEN 'AAAzCldMastMedData-Data_has_Plist'
            ELSE 'AAAzCldMastMedData-Data_Empty-NULL'
        END AS 'AAAzCldMastMedData-Data',
        CASE CMzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Has_CldMastAsset-1'
            WHEN 2 THEN '2-StillTesting-Local_Asset-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || CMzCldMastMedData.Z_OPT || ''
        END AS 'CldMasterzCldMastMedData-zOPT',
        zCldMast.ZMEDIAMETADATATYPE AS 'zCldMast-Media Metadata Type',		
        CASE
            WHEN CMzCldMastMedData.ZDATA > 0 THEN 'CMzCldMastMedData-Data_has_Plist'
            ELSE 'CMzCldMastMedData-Data_Empty-NULL'
        END AS 'CMzCldMastMedData-Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZEXTENDEDATTRIBUTES zExtAttr ON zExtAttr.Z_PK = zAsset.ZEXTENDEDATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA AAAzCldMastMedData ON
             AAAzCldMastMedData.Z_PK = zAddAssetAttr.ZMEDIAMETADATA
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA CMzCldMastMedData ON
             CMzCldMastMedData.Z_PK = zCldMast.ZMEDIAMETADATA
        WHERE (zAsset.ZLATITUDE > 0) OR
          (zExtAttr.ZLATITUDE > 0)
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18],
                                row[19], row[20], row[21], row[22], row[23], row[24]))

                counter += 1

            description = 'Parses basic asset record data from Syndication.photoslibrary-Photos.sqlite for' \
                          ' assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 14. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Syndication_PL_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.2-Has Locations-SyndPL', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zExtAttr-Latitude-2',
                            'zAsset-Longitude-3',
                            'zExtAttr-Longitude-4',
                            'zAddAssetAttr-GPS Horizontal Accuracy-5',
                            'zAsset-Directory-Path-6',
                            'zAsset-Filename-7',
                            'zAddAssetAttr- Original Filename-8',
                            'zCldMast- Original Filename-9',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-10',
                            'zAddAssetAttr-Shifted Location Valid-11',
                            'zAddAssetAttr-Shifted Location Data-12',
                            'zAddAssetAttr-Reverse Location Is Valid-13',
                            'zAddAssetAttr-Reverse Location Data-14',
                            'AAAzCldMastMedData-zOPT-15',
                            'zAddAssetAttr-Media Metadata Type-16',
                            'AAAzCldMastMedData-Data-17',
                            'CldMasterzCldMastMedData-zOPT-18',
                            'zCldMast-Media Metadata Type-19',
                            'CMzCldMastMedData-Data-20',
                            'zAsset-zPK-21',
                            'zAddAssetAttr-zPK-22',
                            'zAsset-UUID = store.cloudphotodb-23',
                            'zAddAssetAttr-Master Fingerprint-24')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.2-Has Locations-SyndPL'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.2-Has Locations-SyndPL'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for Syndication.photoslibrary-Photos.sqlite assets with valid locations')

        db.close()
        return

    elif version.parse(iosversion) >= version.parse("15"):
        file_found = str(files_found[0])
        db = open_sqlite_db_readonly(file_found)
        cursor = db.cursor()

        cursor.execute("""
        SELECT
        DateTime(zAsset.ZDATECREATED + 978307200, 'UNIXEPOCH') AS 'zAsset-Date Created',
        CASE zAsset.ZLATITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLATITUDE
        END AS 'zAsset-Latitude',
        zExtAttr.ZLATITUDE AS 'zExtAttr-Latitude',
        CASE zAsset.ZLONGITUDE
            WHEN -180.0 THEN '-180.0'
            ELSE zAsset.ZLONGITUDE
        END AS 'zAsset-Longitude',
        zExtAttr.ZLONGITUDE AS 'zExtAttr-Longitude',
        CASE zAddAssetAttr.ZGPSHORIZONTALACCURACY
            WHEN -1.0 THEN '-1.0'
            ELSE zAddAssetAttr.ZGPSHORIZONTALACCURACY
        END AS 'zAddAssetAttr-GPS Horizontal Accuracy',
        zAsset.ZDIRECTORY AS 'zAsset-Directory-Path',
        zAsset.ZFILENAME AS 'zAsset-Filename',
        zAddAssetAttr.ZORIGINALFILENAME AS 'zAddAssetAttr- Original Filename',
        zCldMast.ZORIGINALFILENAME AS 'zCldMast- Original Filename',
        zCldMast.ZIMPORTSESSIONID AS 'zCldMast-Import Session ID- AirDrop-StillTesting',
        zAddAssetAttr.ZSYNDICATIONIDENTIFIER AS 'zAddAssetAttr- Syndication Identifier-SWY-Files',
        CASE zAddAssetAttr.ZSHIFTEDLOCATIONISVALID
            WHEN 0 THEN '0-Shifted Location Not Valid-0'
            WHEN 1 THEN '1-Shifted Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZSHIFTEDLOCATIONISVALID || ''
        END AS 'zAddAssetAttr-Shifted Location Valid',
        CASE
            WHEN zAddAssetAttr.ZSHIFTEDLOCATIONDATA > 0 THEN 'zAddAssetAttr-Shifted_Location_Data_has_Plist'
            ELSE 'zAddAssetArrt-Shifted_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Shifted Location Data',
        CASE zAddAssetAttr.ZREVERSELOCATIONDATAISVALID
            WHEN 0 THEN '0-Reverse Location Not Valid-0'
            WHEN 1 THEN '1-Reverse Location Valid-1'
            ELSE 'Unknown-New-Value!: ' || zAddAssetAttr.ZREVERSELOCATIONDATAISVALID || ''
        END AS 'zAddAssetAttr-Reverse Location Is Valid',		
        CASE
            WHEN zAddAssetAttr.ZREVERSELOCATIONDATA > 0 THEN 'zAddAssetAttr-Reverse_Location_Data_has_Plist'
            ELSE 'zAddAssetAttr-Reverse_Location_Data_Empty-NULL'
        END AS 'zAddAssetAttr-Reverse Location Data',
        CASE AAAzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Cloud-1'
            WHEN 2 THEN '2-StillTesting-This Device-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || AAAzCldMastMedData.Z_OPT || ''
        END AS 'AAAzCldMastMedData-zOPT',
        zAddAssetAttr.ZMEDIAMETADATATYPE AS 'zAddAssetAttr-Media Metadata Type',
        CASE
            WHEN AAAzCldMastMedData.ZDATA > 0 THEN 'AAAzCldMastMedData-Data_has_Plist'
            ELSE 'AAAzCldMastMedData-Data_Empty-NULL'
        END AS 'AAAzCldMastMedData-Data',
        CASE CMzCldMastMedData.Z_OPT
            WHEN 1 THEN '1-StillTesting-Has_CldMastAsset-1'
            WHEN 2 THEN '2-StillTesting-Local_Asset-2'
            WHEN 3 THEN '3-StillTesting-Muted-3'
            WHEN 4 THEN '4-StillTesting-Unknown-4'
            WHEN 5 THEN '5-StillTesting-Unknown-5'
            ELSE 'Unknown-New-Value!: ' || CMzCldMastMedData.Z_OPT || ''
        END AS 'CldMasterzCldMastMedData-zOPT',
        zCldMast.ZMEDIAMETADATATYPE AS 'zCldMast-Media Metadata Type',		
        CASE
            WHEN CMzCldMastMedData.ZDATA > 0 THEN 'CMzCldMastMedData-Data_has_Plist'
            ELSE 'CMzCldMastMedData-Data_Empty-NULL'
        END AS 'CMzCldMastMedData-Data',
        zAsset.Z_PK AS 'zAsset-zPK',
        zAddAssetAttr.Z_PK AS 'zAddAssetAttr-zPK',
        zAsset.ZUUID AS 'zAsset-UUID = store.cloudphotodb',
        zAddAssetAttr.ZMASTERFINGERPRINT AS 'zAddAssetAttr-Master Fingerprint'
        FROM ZASSET zAsset
            LEFT JOIN ZADDITIONALASSETATTRIBUTES zAddAssetAttr ON zAddAssetAttr.Z_PK = zAsset.ZADDITIONALATTRIBUTES
            LEFT JOIN ZEXTENDEDATTRIBUTES zExtAttr ON zExtAttr.Z_PK = zAsset.ZEXTENDEDATTRIBUTES
            LEFT JOIN ZCLOUDMASTER zCldMast ON zAsset.ZMASTER = zCldMast.Z_PK
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA AAAzCldMastMedData ON
             AAAzCldMastMedData.Z_PK = zAddAssetAttr.ZMEDIAMETADATA
            LEFT JOIN ZCLOUDMASTERMEDIAMETADATA CMzCldMastMedData ON
             CMzCldMastMedData.Z_PK = zCldMast.ZMEDIAMETADATA
        WHERE (zAsset.ZLATITUDE > 0) OR
          (zExtAttr.ZLATITUDE > 0)
        ORDER BY zAsset.ZDATECREATED
        """)

        all_rows = cursor.fetchall()
        usageentries = len(all_rows)
        data_list = []
        counter = 0
        if usageentries > 0:
            for row in all_rows:
                data_list.append((row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9],
                                row[10], row[11], row[12], row[13], row[14], row[15], row[16], row[17], row[18],
                                row[19], row[20], row[21], row[22], row[23], row[24], row[25]))

                counter += 1

            description = 'Parses basic asset record data from Syndication.photoslibrary-Photos.sqlite for' \
                          ' assets that have valid' \
                          ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields' \
                          ' and supports iOS 15-17. The results for this script will contain' \
                          ' one record per ZASSET table Z_PK value.'
            report = ArtifactHtmlReport('Photos.sqlite-Syndication_PL_Artifacts')
            report.start_artifact_report(report_folder, 'Ph5.2-Has Locations-SyndPL', description)
            report.add_script()
            data_headers = ('zAsset-Date Created-0',
                            'zAsset-Latitude-1',
                            'zExtAttr-Latitude-2',
                            'zAsset-Longitude-3',
                            'zExtAttr-Longitude-4',
                            'zAddAssetAttr-GPS Horizontal Accuracy-5',
                            'zAsset-Directory-Path-6',
                            'zAsset-Filename-7',
                            'zAddAssetAttr- Original Filename-8',
                            'zCldMast- Original Filename-9',
                            'zCldMast-Import Session ID- AirDrop-StillTesting-10',
                            'zAddAssetAttr- Syndication Identifier-SWY-Files-11',
                            'zAddAssetAttr-Shifted Location Valid-12',
                            'zAddAssetAttr-Shifted Location Data-13',
                            'zAddAssetAttr-Reverse Location Is Valid-14',
                            'zAddAssetAttr-Reverse Location Data-15',
                            'AAAzCldMastMedData-zOPT-16',
                            'zAddAssetAttr-Media Metadata Type-17',
                            'AAAzCldMastMedData-Data-18',
                            'CldMasterzCldMastMedData-zOPT-19',
                            'zCldMast-Media Metadata Type-20',
                            'CMzCldMastMedData-Data-21',
                            'zAsset-zPK-22',
                            'zAddAssetAttr-zPK-23',
                            'zAsset-UUID = store.cloudphotodb-24',
                            'zAddAssetAttr-Master Fingerprint-25')
            report.write_artifact_data_table(data_headers, data_list, file_found)
            report.end_artifact_report()

            tsvname = 'Ph5.2-Has Locations-SyndPL'
            tsv(report_folder, data_headers, data_list, tsvname)

            tlactivity = 'Ph5.2-Has Locations-SyndPL'
            timeline(report_folder, tlactivity, data_list, data_headers)

        else:
            logfunc('No data available for Syndication.photoslibrary-Photos.sqlite assets with valid locations')

        db.close()
        return


__artifacts_v2__ = {
    'Ph5-1-Assets have valid locations-PhDaPsql': {
        'name': 'PhDaPL Photos.sqlite 5.1 assets have locations',
        'description': 'Parses basic asset record data from PhotoData-Photos.sqlite for assets that have valid'
                       ' locations from the ZASSET and ZEXTENDEDATTRIBUTES table ZLATITUDE fields'
                       ' and supports iOS 11-17. The results for this script will contain'
                       ' one record per ZASSET table Z_PK value.',
        'author': 'Scott Koenig https://theforensicscooter.com/',
        'version': '1.3',
        'date': '2024-04-13',
        'requirements': 'Acquisition that contains PhotoData-Photos.sqlite',
        'category': 'Photos.sqlite-Other_Artifacts',
        'notes': '',
        'paths': '*/mobile/Media/PhotoData/Photos.sqlite*',
        'function': 'get_ph5haslocationsphdapsql'
    },
    'Ph5-2-Assets have valid locations-SyndPL': {
        'name': 'SyndPL Photos.sqlite 5.2 assets have locations',
        'description': 'Parses basic asset record data from Syndication.photoslibrary-database-Photos.sqlite'
                       ' for assets that have valid locations from the ZASSET and ZEXTENDEDATTRIBUTES table'
                       ' ZLATITUDE fields and supports iOS 11-17. The results for this script will contain'
                       ' one record per ZASSET table Z_PK value.',
        'author': 'Scott Koenig https://theforensicscooter.com/',
        'version': '1.3',
        'date': '2024-04-13',
        'requirements': 'Acquisition that contains Syndication Photo Library Photos.sqlite',
        'category': 'Photos.sqlite-Syndication_PL_Artifacts',
        'notes': '',
        'paths': '*/mobile/Library/Photos/Libraries/Syndication.photoslibrary/database/Photos.sqlite*',
        'function': 'get_ph5haslocationssyndpl'
    }
}
