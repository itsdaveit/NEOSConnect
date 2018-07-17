# -*- coding: utf-8 -*-
# Copyright (c) 2018, itsdave GmbH and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from zeep import Client
from zeep.plugins import HistoryPlugin
import xml.etree.ElementTree as ET
import pprint


class NEOSConnectAPI(Document):

    def process_NEOS_getSuppliers_Response(self, suppliers_response):
        suppliers_list = []
        for supplier in suppliers_response:
            supplier_dict = {}
            supplier_dict["sup_id"] = supplier["sup_id"]
            supplier_dict["sup_name"] = supplier["sup_name"]
            supplier_dict["sup_company"] = supplier["sup_company"]
            supplier_dict["customer_id"] = supplier["customer_id"]
            supplier_dict["amount"] = float(supplier["shipment"]["amount"])
            supplier_dict["free_from"] = float(supplier["shipment"]["free_from"])
            supplier_dict["min_amount"] = float(supplier["shipment"]["min_amount"])
            supplier_dict["min_to"] = float(supplier["shipment"]["min_to"])
            supplier_dict["min_order_value"] = float(supplier["shipment"]["min_order_value"])
            supplier_dict["extra_amount1"] = float(supplier["shipment"]["extra_amount1"])
            supplier_dict["extra_type1"] = supplier["shipment"]["extra_type1"]
            supplier_dict["extra_amount2"] = float(supplier["shipment"]["extra_amount2"])
            supplier_dict["extra_type2"] = supplier["shipment"]["extra_type2"]

            suppliers_list.append(supplier_dict)
        return suppliers_list

    def set_NEOSSuppliers(self, suppliers_dict):
        #Fügt "NEOS Lieferant" ein und aktualisiert, wenn Änderungen gefnuden werden.
        #Die Lieferanten ID aus NEOS wird als Index verwendet
        count_NEOS_Lieferanten = 0
        for supplier in suppliers_dict:
            found_suppliers = frappe.get_all("NEOS Lieferant", filters={"sup_id": supplier["sup_id"] })
            if len(found_suppliers) > 1:
                frappe.throw("Doppelte sup_id " + supplier["sup_id"])

            elif len(found_suppliers) == 1:

                #print "NEOS Lieferant mit sup_id " + str(supplier["sup_id"]) + " existiert bereits. Vergleiche."
                #Update der Daten
                NEOS_Lieferant = frappe.get_doc("NEOS Lieferant", found_suppliers[0].name )
                change_detected = False

                if NEOS_Lieferant.sup_name != supplier["sup_name"]:
                    NEOS_Lieferant.sup_name = supplier["sup_name"]
                    change_detected = True

                if NEOS_Lieferant.sup_company != supplier["sup_company"]:
                    NEOS_Lieferant.sup_company = supplier["sup_company"]
                    change_detected = True

                if NEOS_Lieferant.customer_id != supplier["customer_id"]:
                    NEOS_Lieferant.customer_id = supplier["customer_id"]
                    change_detected = True

                if NEOS_Lieferant.amount != supplier["amount"]:
                    NEOS_Lieferant.amount = supplier["amount"]
                    change_detected = True

                if NEOS_Lieferant.free_from != supplier["free_from"]:
                    NEOS_Lieferant.free_from = supplier["free_from"]
                    change_detected = True

                if NEOS_Lieferant.min_amount != supplier["min_amount"]:
                    NEOS_Lieferant.min_amount = supplier["min_amount"]
                    change_detected = True

                if NEOS_Lieferant.min_to != supplier["min_to"]:
                    NEOS_Lieferant.min_to = supplier["min_to"]
                    change_detected = True

                if NEOS_Lieferant.min_order_value != supplier["min_order_value"]:
                    NEOS_Lieferant.min_order_value = supplier["min_order_value"]
                    change_detected = True

                if NEOS_Lieferant.extra_amount1 != supplier["extra_amount1"]:
                    NEOS_Lieferant.extra_amount1 = supplier["extra_amount1"]
                    change_detected = True

                if NEOS_Lieferant.extra_type1 != supplier["extra_type1"]:
                    NEOS_Lieferant.extra_type1 = supplier["extra_type1"]
                    change_detected = True

                if NEOS_Lieferant.extra_amount2 != supplier["extra_amount2"]:
                    NEOS_Lieferant.extra_amount2 = supplier["extra_amount2"]
                    change_detected = True

                if NEOS_Lieferant.extra_type2 != supplier["extra_type2"]:
                    NEOS_Lieferant.extra_type2 = supplier["extra_type2"]
                    change_detected = True

                count_NEOS_Lieferanten += 1

                if change_detected:
                    print("Aenderung gefunden.")
                    NEOS_Lieferant.save()


            else:
                #Neuanlage des Lieferanten
                item_doc = frappe.get_doc({"doctype": "NEOS Lieferant",
                "sup_name": supplier["sup_name"],
                "sup_company": supplier["sup_company"],
                "sup_id": supplier["sup_id"],
                "customer_id": supplier["customer_id"],
                "amount": supplier["amount"],
                "free_from": supplier["free_from"],
                "min_amount": supplier["min_amount"],
                "min_to": supplier["min_to"],
                "min_order_value": supplier["min_order_value"],
                "extra_amount1": supplier["extra_amount1"],
                "extra_type1": supplier["extra_type1"],
                "extra_amount2": supplier["extra_amount2"],
                "extra_type2": supplier["extra_type2"],
                })
                print item_doc.insert().sup_name + " Angelegt"
                count_NEOS_Lieferanten += 1

        return count_NEOS_Lieferanten


    def set_ERPNextSuppliers(self):
        count_ERPNextSuppliers = 0

        found_NEOS_Lieferanten = frappe.get_all("NEOS Lieferant")
        if len(found_NEOS_Lieferanten) >= 1:
            found_ERPNext_Suppliers = frappe.get_all("Supplier", filters={"supplier_type": "NEOS Lieferant" })
            count_ERPNextSuppliers = len(found_ERPNext_Suppliers)
            for NEOS_Lieferant in found_NEOS_Lieferanten:
                NEOS_Lieferant_doc = frappe.get_doc("NEOS Lieferant", NEOS_Lieferant.name)

                if NEOS_Lieferant_doc.supplier == None:
                    supplier_doc = frappe.get_doc({"doctype": "Supplier",
                    "supplier_name": NEOS_Lieferant_doc.sup_company,
                    "supplier_type": "NEOS Lieferant",})
                    inerted_ERPNext_Supplier = supplier_doc.insert()
                    NEOS_Lieferant_doc.supplier = inerted_ERPNext_Supplier.name
                    NEOS_Lieferant_doc.save()

                else:
                    change_detected = False
                    ERPNext_Supplier_doc = frappe.get_doc("Supplier", NEOS_Lieferant_doc.supplier)

                    if ERPNext_Supplier_doc.supplier_name != NEOS_Lieferant_doc.sup_company:
                        ERPNext_Supplier_doc.supplier_name = NEOS_Lieferant_doc.sup_company
                        change_detected = True

                    if change_detected:
                        print("Aenderung gefunden.")
                        ERPNext_Supplier_doc.save()

            return count_ERPNextSuppliers


    def neos_getSuppliers(self):
        NEOSConnect_settings = frappe.get_doc("NEOSConnect Settings")
        NEOSClient = Client(NEOSConnect_settings.neos_wsdl_url, strict=False)

        request_data = {
        "username": NEOSConnect_settings.neos_user,
        "password": NEOSConnect_settings.neos_password,
        "active": True}

        request_data["sid"] = (NEOSClient.service.getSessionID(request_data))
        suppliers_response = (NEOSClient.service.getSuppliers(request_data))["item"]
        suppliers_list = self.process_NEOS_getSuppliers_Response(suppliers_response)
        if len(suppliers_list) >= 1:
            count_NEOS_Lieferanten = self.set_NEOSSuppliers(suppliers_list)
        else:
            frappe.throw("NEOS Antwort enthielt keine Lieferanten.")

        if count_NEOS_Lieferanten >= 1:
            count_ERPNext_Lieferanten = self.set_ERPNextSuppliers()
        else:
            frappe.throw("Keine NEOS Lieferanten vorhanden.")

        frappe.msgprint("Vorgang Erfolgreich.")
        frappe.msgprint(str(count_NEOS_Lieferanten) + " NEOS Lieferanten vorhanden.")
        frappe.msgprint(str(count_ERPNext_Lieferanten) + " ERPNext Lieferanten vorhanden.")
