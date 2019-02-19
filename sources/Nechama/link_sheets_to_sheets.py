#encoding=utf-8

import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import re
from sources.local_settings import *
from sources.functions import post_sheet, http_request

POST_SERVER = "http://einmishpat.sandbox.sefaria.org"
def get_ssn(read_id):
    """
    gets a sheet id from a server and maps it to the correct ssn (using tags)
    :param read_id: Sheet id
    :return: ssn
    """
    map_get_id_ssn = {x: x for x in range(1478)}
    # map_get_id_ssn = {1216: 249, 1217: 248, 1218: 247, 1219: 246, 1220: 245, 1221: 244, 1222: 243, 1223: 242, 1224: 241, 1225: 240, 1226: 239, 1228: 238, 1229: 237, 1230: 236, 1231: 235, 1232: 234, 1233: 233, 1234: 232, 1235: 231, 1236: 230, 1237: 229, 1238: 228, 1239: 227, 1240: 226, 1241: 225, 1243: 224, 1244: 223, 1245: 222, 1246: 221, 1247: 220, 1248: 219, 1249: 218, 1250: 217, 1251: 216, 1252: 215, 1253: 214, 1254: 213, 1255: 212, 1256: 211, 1257: 210, 1258: 209, 1259: 208, 1260: 207, 1261: 206, 1262: 205, 1263: 204, 1264: 203, 1265: 202, 1266: 201, 1267: 200, 1268: 199, 1269: 198, 1270: 197, 1271: 196, 1272: 195, 1273: 194, 1274: 193, 1275: 192, 1276: 191, 1277: 190, 1278: 189, 1279: 188, 1280: 187, 1281: 186, 1282: 185, 1283: 184, 1284: 183, 1285: 182, 1286: 181, 1287: 180, 1288: 179, 1289: 178, 1290: 177, 1291: 176, 1292: 175, 1293: 174, 1294: 173, 1295: 172, 1296: 171, 1297: 170, 1298: 169, 1299: 168, 1300: 167, 1301: 166, 1302: 165, 1303: 164, 1304: 163, 1305: 162, 1306: 161, 1307: 160, 1308: 159, 1309: 158, 1310: 157, 1311: 156, 1312: 155, 1313: 154, 1314: 153, 1315: 152, 1316: 151, 1317: 150, 1318: 149, 1319: 148, 1320: 147, 1321: 146, 1322: 145, 1323: 144, 1324: 143, 1325: 142, 1326: 141, 1327: 140, 1328: 139, 1329: 138, 1330: 137, 1331: 136, 1332: 135, 1333: 134, 1334: 133, 1335: 132, 1336: 131, 1337: 130, 1338: 129, 1339: 128, 1340: 127, 1341: 126, 1342: 125, 1343: 124, 1344: 123, 1345: 122, 1346: 121, 1348: 120, 1349: 119, 1350: 118, 1351: 117, 1352: 116, 1353: 115, 1354: 114, 1355: 113, 1356: 112, 1357: 111, 1359: 110, 1360: 109, 1361: 108, 1362: 107, 1363: 106, 1364: 105, 1365: 104, 1366: 103, 1367: 102, 1368: 101, 1369: 100, 1370: 99, 1371: 98, 1372: 97, 1373: 96, 1374: 95, 1375: 94, 1376: 93, 1377: 92, 1378: 91, 1379: 90, 1380: 89, 1381: 88, 1382: 87, 1383: 86, 1384: 85, 1385: 84, 1386: 83, 1387: 82, 1388: 81, 1389: 80, 1390: 79, 1391: 78, 1392: 77, 1393: 76, 1394: 75, 1395: 74, 1396: 73, 1397: 72, 1398: 71, 1399: 70, 1400: 69, 1401: 68, 1402: 67, 1403: 66, 1404: 65, 1405: 64, 1406: 63, 1407: 62, 1408: 61, 1409: 60, 1410: 59, 1411: 58, 1412: 57, 1413: 56, 1414: 55, 1415: 54, 1416: 53, 1417: 52, 1418: 51, 1419: 50, 1420: 49, 1421: 48, 1422: 47, 1423: 46, 1424: 45, 1425: 44, 1426: 43, 1427: 42, 1428: 41, 1429: 40, 1430: 39, 1431: 38, 1432: 37, 1433: 36, 1434: 35, 1435: 34, 1436: 33, 1437: 32, 1438: 31, 1439: 30, 1440: 29, 1441: 28, 1442: 27, 1443: 26, 1444: 25, 1445: 24, 1446: 23, 1447: 22, 1448: 21, 1449: 20, 1450: 19, 1451: 18, 1452: 17, 1455: 16, 1456: 15, 1457: 14, 1458: 13, 1459: 12, 1461: 11, 1464: 10, 1465: 9, 1466: 8, 1467: 7, 1468: 6, 1469: 5, 1472: 4, 1473: 3, 1474: 2, 1478: 1
    # }  # this is a map id -> ssn in the server db we are copying from
    ssn = map_get_id_ssn.get(int(read_id), 0)
    return ssn

def get_post_id(ssn):
    """
    for the post server gets a ssn and returns the id to which the sheet should be connected. based on the ssn<->id mapping
    on the post server which we learn from the ssn tags
    :param ssn:
    :return:
    """
    map_post_ssn_id = {1216: 249, 1217: 248, 1218: 247, 1219: 246, 1220: 245, 1221: 244, 1222: 243, 1223: 242, 1224: 241, 1225: 240, 1226: 239, 1228: 238, 1229: 237, 1230: 236, 1231: 235, 1232: 234, 1233: 233, 1234: 232, 1235: 231, 1236: 230, 1237: 229, 1238: 228, 1239: 227, 1240: 226, 1241: 225, 1243: 224, 1244: 223, 1245: 222, 1246: 221, 1247: 220, 1248: 219, 1249: 218, 1250: 217, 1251: 216, 1252: 215, 1253: 214, 1254: 213, 1255: 212, 1256: 211, 1257: 210, 1258: 209, 1259: 208, 1260: 207, 1261: 206, 1262: 205, 1263: 204, 1264: 203, 1265: 202, 1266: 201, 1267: 200, 1268: 199, 1269: 198, 1270: 197, 1271: 196, 1272: 195, 1273: 194, 1274: 193, 1275: 192, 1276: 191, 1277: 190, 1278: 189, 1279: 188, 1280: 187, 1281: 186, 1282: 185, 1283: 184, 1284: 183, 1285: 182, 1286: 181, 1287: 180, 1288: 179, 1289: 178, 1290: 177, 1291: 176, 1292: 175, 1293: 174, 1294: 173, 1295: 172, 1296: 171, 1297: 170, 1298: 169, 1299: 168, 1300: 167, 1301: 166, 1302: 165, 1303: 164, 1304: 163, 1305: 162, 1306: 161, 1307: 160, 1308: 159, 1309: 158, 1310: 157, 1311: 156, 1312: 155, 1313: 154, 1314: 153, 1315: 152, 1316: 151, 1317: 150, 1318: 149, 1319: 148, 1320: 147, 1321: 146, 1322: 145, 1323: 144, 1324: 143, 1325: 142, 1326: 141, 1327: 140, 1328: 139, 1329: 138, 1330: 137, 1331: 136, 1332: 135, 1333: 134, 1334: 133, 1335: 132, 1336: 131, 1337: 130, 1338: 129, 1339: 128, 1340: 127, 1341: 126, 1342: 125, 1343: 124, 1344: 123, 1345: 122, 1346: 121, 1348: 120, 1349: 119, 1350: 118, 1351: 117, 1352: 116, 1353: 115, 1354: 114, 1355: 113, 1356: 112, 1357: 111, 1359: 110, 1360: 109, 1361: 108, 1362: 107, 1363: 106, 1364: 105, 1365: 104, 1366: 103, 1367: 102, 1368: 101, 1369: 100, 1370: 99, 1371: 98, 1372: 97, 1373: 96, 1374: 95, 1375: 94, 1376: 93, 1377: 92, 1378: 91, 1379: 90, 1380: 89, 1381: 88, 1382: 87, 1383: 86, 1384: 85, 1385: 84, 1386: 83, 1387: 82, 1388: 81, 1389: 80, 1390: 79, 1391: 78, 1392: 77, 1393: 76, 1394: 75, 1395: 74, 1396: 73, 1397: 72, 1398: 71, 1399: 70, 1400: 69, 1401: 68, 1402: 67, 1403: 66, 1404: 65, 1405: 64, 1406: 63, 1407: 62, 1408: 61, 1409: 60, 1410: 59, 1411: 58, 1412: 57, 1413: 56, 1414: 55, 1415: 54, 1416: 53, 1417: 52, 1418: 51, 1419: 50, 1420: 49, 1421: 48, 1422: 47, 1423: 46, 1424: 45, 1425: 44, 1426: 43, 1427: 42, 1428: 41, 1429: 40, 1430: 39, 1431: 38, 1432: 37, 1433: 36, 1434: 35, 1435: 34, 1436: 33, 1437: 32, 1438: 31, 1439: 30, 1440: 29, 1441: 28, 1442: 27, 1443: 26, 1444: 25, 1445: 24, 1446: 23, 1447: 22, 1448: 21, 1449: 20, 1450: 19, 1451: 18, 1452: 17, 1455: 16, 1456: 15, 1457: 14, 1458: 13, 1459: 12, 1461: 11, 1464: 10, 1465: 9, 1466: 8, 1467: 7, 1468: 6, 1469: 5, 1472: 4, 1473: 3, 1474: 2, 1478: 1
                       }
    # map_post_ssn_id = {y: x for x, y in map_post_id_ssn.iteritems()}
    post_id = map_post_ssn_id.get(ssn, 0)
    return post_id

def get_sheets_from_get_server(list_get_sheet_ids, get_server_address):
    got_sheets = []
    for id in list_get_sheet_ids:
        url = get_server_address + "/api/sheets/{}".format(id)
        got = http_request(url, body={"apikey": API_KEY}, method="GET")
        got_sheets.append(got)
    return got_sheets
    
    
    
if __name__ == "__main__":
    #use list of which sheets have links which has sheet title and sheet year and tags
    #for each sheet, get each segment and check if it has
    sheet_data = []
    # sheets = db.sheets.find({"tags": "UI"})
    compile = re.compile(u'/sheets/(?P<id>\d+)')  # (?:\.(?P<node>\d+))?
    sheets = get_sheets_from_get_server([2], "http://einmishpat.sandbox.sefaria.org")  # list_get_sheet_ids comes straight from mongo
    for sheet_json in sheets:
        for i, s in enumerate(sheet_json['sources']):
            compile = re.compile(u'/sheets/(?P<id>\d+)')  # (?:\.(?P<node>\d+))?
            if 'outsideText' in s.keys():
                uni_outsidetext = unicode(s['outsideText'], encoding='utf8') if isinstance(s['outsideText'],str) else s['outsideText']
                matched = re.search(compile, s['outsideText'])
                if matched:
                    ssn = get_ssn(matched.group("id")) # this is the ssn of the sheet to connect to
                    to_post_id = get_post_id(ssn)
                    new_link = re.sub(compile, u'/sheets/{}'.format(to_post_id), s['outsideText'])
                    s['outsideText'] = re.sub(compile, u'/sheets/\g<id>', new_link) #todo: check and then test this line
            elif 'outsideBiText' in s.keys():
                uni_outsidetext = unicode(s['outsideBiText']['he'], encoding='utf8') if isinstance(s['outsideBiText']['he'], str) else \
                s['outsideBiText']['he']
                matched = re.search(compile, s['outsideBiText'])
                if matched:
                    ssn = get_ssn(matched.group("id"))
                    to_post_id = get_post_id(ssn)
                    new_link = re.sub(compile, u'/sheets/{}'.format(to_post_id), s['outsideText'])
                    s['outsideBiText'] = re.sub(compile, u'/sheets/\g<id>', new_link) #todo: check and then test this line
        del sheet_json['_id']
        post_sheet(sheet_json, POST_SERVER)  # notice it is posting with the original id hence it is looking to repost on the same server it read from
        # the changes are with the linking that has changed after we posted all.
    # for title_year_tags in sheet_data:
    #     title, year, tags = title_year_tags
    #     sheet = db.sheets.find({"title": title, "summary": year, "tags": tags})
    #     assert sheet, u"Couldn't find sheet {}".format(title)
    #     for segment in sheet["sources"]:
    #         text = segment["text"]["he"] if "text" in segment.keys() else segment["outsideText"]
    #         for match in re.findall("^<a href.*?nechama.org.il/pages/.*?</a>", text):
    #             text = text.replace(match, )



