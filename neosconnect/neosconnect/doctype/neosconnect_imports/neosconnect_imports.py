# -*- coding: utf-8 -*-
# Copyright (c) 2018, itsdave GmbH and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe.model.document import Document
from frappe.utils import csvutils
import frappe
import glob
import os
import csv


class NEOSConnectimports(Document):
    def import_from_csv_folder(self):
        NEOSConnect_settings = frappe.get_doc("NEOSConnect Settings")
        #CSV Headers, which we expect
        csv_headers = {}
        csv_headers['NEOS_note'] = ["map_id", "man_name", "man_aid", "desc_short", "price_min", "price_special", "qty_status_max", "item_remarks", "user_name", "sup_name", "sup_id", "sup_aid", "price_amount", "qty_status", "item_qty", "vk_netto"]
        csv_headers['NEOS_order'] = ["map_id", "sup_name", "sup_id", "sup_aid", "man_name", "man_aid", "desc_short", "ean", "price_requested", "price_confirmed", "qty_requested", "qty_confirmed", "qty_delivered", "item_remark", "user_name", "reference", "customer_po", "order_name", "order_date", "response_date", "order_status"]
        print "#####################################"

        if NEOSConnect_settings.csv_import_folder != "":
            files = []
            for file in os.listdir(NEOSConnect_settings.csv_import_folder):
                current_file = os.path.join(NEOSConnect_settings.csv_import_folder, file)
                #NEOS Merkzettel
                if file.startswith("note_") & file.endswith(".csv"):
                    files.append(current_file)
                    self.process_csv(current_file, "NEOS_note", NEOSConnect_settings, csv_headers)
                #NEOS Bestellungen
                if file.startswith("order_") & file.endswith(".csv"):
                    files.append(current_file)
                    self.process_csv(current_file, "NEOS_order", NEOSConnect_settings, csv_headers)
            if len(files) == 0:
                frappe.throw("No files found in directory " + NEOSConnect_settings.csv_import_folder)

        else:
            frappe.throw("CSV directory error")

    def process_csv(self, csv_filename, file_type, NEOSConnect_settings, csv_headers):
            print "processing " + csv_filename + " as " + file_type
            csv_rows = []
            with open(csv_filename, 'r') as csv_file:
                spamreader = csv.reader(csv_file, delimiter=str(u';'), quotechar=str(u'"'))
                for row in spamreader:
                    csv_rows.append(row)

            if self.check_csv_format(csv_rows, file_type, csv_headers):
                print "CSV check OK"
                csv_rows.pop(0)
                for row in csv_rows:
                    item_data = self.assign_item_data(row, csv_headers[file_type])
                    print item_data
                    self.create_item(item_data, NEOSConnect_settings)
            else:
                frappe.throw("Fehler in CSV Datei " + csv_filename)

    def assign_item_data(self, row, csv_header):
        keys = []
        for key in csv_header:
            keys.append(key)
        values = []
        for value in row:
            value = value.decode("iso-8859-1")
            values.append(value)
        item_data = dict(zip(keys, values))
        return item_data


    def create_item(self, item_data, NEOSConnect_settings):

        item_code = "MAPID-" + item_data["map_id"]
        found_items = frappe.get_all("Item", filters={"item_code": item_code }, fields=["name", "item_code"] )
        if len(found_items) >= 1:
            print "Item " + item_code + " allready exists."

        else:
            item_doc = frappe.get_doc({"doctype": "Item",
            "item_code": item_code,
            "item_group": NEOSConnect_settings.destination_item_group,
            "item_name": item_data["desc_short"]
            })
            item_doc.insert()


    def check_csv_format(self, csv_rows, file_type, csv_headers):
        #NEOS Merkzelltel Format prüfen
        if file_type == "NEOS_note":
            if csv_rows[0] == csv_headers["NEOS_note"]:
                if len(csv_rows) > 1:
                    return True,
        #NEOS Bestellung Format prüfen
        if file_type == "NEOS_order":
            if csv_rows[0] == csv_headers["NEOS_order"]:
                if len(csv_rows) > 1:
                    return True,
        return False
