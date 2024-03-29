# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from report import report_sxw
import datetime
from tools import DEFAULT_SERVER_DATE_FORMAT

class invoice_format_a(report_sxw.rml_parse):
    
    def __init__(self,cr,uid,name,context):
        super(invoice_format_a,self).__init__(cr,uid,name,context=context)
        self.amount_total = self.amount_13_total = 0.0
        self.localcontext.update({
            'get_period_month': self.get_period_month,
            'get_current_year': self.get_current_year,
            'get_invoice_data': self.get_invoice_data,
            'get_amount_total': self.get_amount_total,
            'get_amount_13_total': self.get_amount_13_total,
            'get_company_name': self.get_company_name,
            'get_company_nit': self.get_company_nit,
            'get_company_address': self.get_company_address
        })

    def get_company_address(self):
        user_data = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        company_address = user_data.company_id.street + ' ' + user_data.company_id.street2 or ''
        return company_address

    def get_company_nit(self):
        user_data = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        company_nit = user_data.company_id.partner_id.nit or ''
        return company_nit

    def get_company_name(self):
        user_data = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        company_name = user_data.company_id.name or ''
        return company_name

    def get_amount_total(self):
        return self.amount_total

    def get_amount_13_total(self):
        return self.amount_13_total

    def get_invoice_data(self, form):
        period = self.pool.get('account.period').browse(self.cr, self.uid, form['period_id'][0])
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(self.cr, self.uid, [('date_invoice','>=', period.date_start),('date_invoice','<=', period.date_stop)])
        invoice_list = []
        for invoice in invoice_obj.browse(self.cr, self.uid, invoice_ids):
            res = {
                'date': datetime.datetime.strptime(invoice.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime('%d/%m/%Y') or '',
                'nit': invoice.nit or '',
                'legal_name_customer': invoice.legal_customer_name or '',
                'invoice_no': invoice.qr_invoice_no or '',
                'invoice_authorization': invoice.qr_code_id.auth_number or '',
                'control_code': invoice.control_code,
                'amount': invoice.amount_total,
                'amount_13': invoice.amt_thirteen
            }
            self.amount_13_total += invoice.amt_thirteen
            self.amount_total += invoice.amount_total
            invoice_list.append(res)
        return invoice_list

    def get_period_month(self, form):
        period = self.pool.get('account.period').browse(self.cr, self.uid, form['period_id'][0])
        current_month = datetime.datetime.strptime(period.date_start, DEFAULT_SERVER_DATE_FORMAT).strftime('%m')
        return current_month

    def get_current_year(self, form):
        period = self.pool.get('account.period').browse(self.cr, self.uid, form['period_id'][0])
        current_year = period.fiscalyear_id.name
        return current_year


report_sxw.report_sxw('report.invoice_format_a','account.invoice','addons/account_invoice_report/report/invoice_format_a.rml',parser=invoice_format_a, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: