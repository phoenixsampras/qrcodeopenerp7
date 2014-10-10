# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Poiesis Consulting (<http://www.poiesisconsulting.com>).
#    Autor: Nicolas Bustillos
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from osv import osv
from osv import fields
from BeautifulSoup import BeautifulSoup
import subprocess
import urllib, urllib2
from urllib import urlencode
import decimal_precision as dp
import re
import datetime
from tools import DEFAULT_SERVER_DATE_FORMAT
from httplib2 import Http


class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def _count_amt(self, cr, uid, ids, name, args, context=None):
        result = {}
        for data in self.browse(cr, uid, ids, context):
            result[data.id] = data.amount_total * 0.13 or 0.00
        return result

    def _count_control_code(self, cr, uid, ids, name, args, context=None):
        result = {}
        date = False
        for data in self.browse(cr, uid, ids, context):
            if data.date_invoice:
                date = datetime.datetime.strptime(data.date_invoice, DEFAULT_SERVER_DATE_FORMAT).strftime('%Y%m%d')
            h = Http()
            url_data = dict(AUTH_NUMBER=int(data.qr_code_id.auth_number),INVOICE_NUMBER=int(data.qr_invoice_no),NIT_CODE_CUSTOMER=int(data.nit),DATE=int(date),AMOUNT=data.amount_total,KEYGEN=str(data.qr_code_id.keygen or ''))
            url= urlencode(url_data)
            resp = urllib2.urlopen('http://198.178.122.145:8060/cc/codigo_control.php?'+url)
            soup = BeautifulSoup(resp)
            result[data.id] = str(soup) or ''
        return result

    def _get_month_first_date(self, cr, uid, ids, name, args, context=None):
        result = {}
        for data in self.browse(cr, uid, ids):
            today_date = datetime.date.today().strftime('%d')
            if today_date == 1:
                seq = {
                    'name': 'QR Customer Invoice',
                    'implementation':'standard',
                    'code': 'account.invoice',
                    'prefix': '',
                    'padding': 1,
                    'number_increment': 1
                }
                self.pool.get('ir.sequence').create(cr, uid, seq)
            result[data.id] = today_date
        return result

    def _get_qr_code(self, cr, uid, ids, context=None):
        qr_code_ids = self.pool.get('account.invoice').search(cr, uid, [('qr_code_id', 'in', ids)], context=context)
        return qr_code_ids

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    _columns = {
        'shop_id': fields.many2one('sale.shop', 'Shop'),
        'qr_code_id': fields.many2one('qr.code', 'Dosificacion Tienda'),
        'nit': fields.char('NIT', size=11),
        'legal_customer_name': fields.char('Legal Name Customer', size=32),
        'razon': fields.char('Razón Social',size=124,help="Nombre o Razón Social para la Factura."),
        'amt_thirteen': fields.function(_count_amt, string="Amount*0.13", type='float'),
        'control_code': fields.function(_count_control_code, string="Control Code", type='char', size=17, store=
                                        {
                                        'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['qr_code_id', 'nit', 'date_invoice', 'qr_invoice_no', 'amount_total'], 10),
                                        'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
                                        'qr.code': (_get_qr_code, ['auth_number', 'keygen', 'nit_code_comapny'], 10),
                                    }
                                        ),
        'qr_invoice_no': fields.char('QR Invoice Number', size=32),
        'get_month_first_date': fields.function(_get_month_first_date, string="Month Date", type="integer")
    }

    _defaults = {
        'qr_invoice_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'account.invoice'),
    }

    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        domain = {}
        data = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context)
        qr_code_ids = [qr.id for qr in data.qr_code_ids]
        domain = [('id', '=', qr_code_ids)]
        return {'domain': {'qr_code_id': domain}}

    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
        date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        result = super(account_invoice,self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        if partner_id:
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            result['value']['nit'] = p.commercial_partner_id.nit
            result['value']['legal_customer_name'] = p.legal_name_customer
        return result

    def print_qr_report(self, cr, uid, ids, context):
        for data in self.browse(cr, uid, ids):
            if data.qr_code_id.print_formate == 'original_a':
                datas = {
                    'ids': ids,
                    'model': 'account.invoice',
                    'form': self.read(cr, uid, ids[0], context=context)
                }
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'factura_receipt',
                    'datas': datas,
                    'nodestroy' : True
                }
            if data.qr_code_id.print_formate == 'original_b':
                datas = {
                    'ids': ids,
                    'model': 'account.invoice',
                    'form': self.read(cr, uid, ids[0], context=context)
                }
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'anverso_receipt',
                    'datas': datas,
                    'nodestroy' : True
                }

class sale_shop(osv.osv):
    _inherit = 'sale.shop'
    _columns = {
        'qr_code_ids': fields.many2many('qr.code', 'invoice_qr_code_rel', 'invoice_id', 'qr_id', 'Dosificacion Tienda'),
    }
sale_shop()

class qr_code(osv.osv):
    _name = 'qr.code'
    _rec_name = 'nit_code_comapny'

    _columns = {
        'nit_code_comapny': fields.char('NIT Code Company', size=50),
        'company_name': fields.many2one('res.company', 'Company'),
        'invoice_number': fields.integer('Inovice Number', size=10),
        'invoice_authorization': fields.integer('Inovice Authorization', size=15),
        'qr_date': fields.date('Date'),
        'amount': fields.float('Amount', size=11),
        'date_limit': fields.date('Date Limit'),
        'ice': fields.integer('ICE'),
        'ivg': fields.integer('IVG'),
        'nit_code_customer': fields.char('NIT Code Customer', size=12),
        'legal_customer_name': fields.char('Legal Name Customer', size=255),
        'auth_number': fields.char('Auth Number', size=32),
        'keygen': fields.char('Keygen', size=255),
        'code': fields.char('Code', size=32),
        'street1': fields.char('Street1', size=32),
        'street2': fields.char('Street2', size=32),
        'phone': fields.integer('Phone'),
        'city': fields.char('City', size=32),
        'description': fields.text('Description'),
        'slogan': fields.char('Slogan', size=255),
        'print_formate': fields.selection([('original_a', 'Original A'), ('original_b', 'Original B')], string="Print Formate", required=True)
    }
    