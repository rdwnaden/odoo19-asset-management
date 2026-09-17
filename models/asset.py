# -*- coding: utf-8 -*-
import io
import base64
import xlsxwriter
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Asset(models.Model):
    _name = 'itsm.asset'
    _inherit = ["mail.thread","mail.activity.mixin"]
    _description = 'Asset'

    name = fields.Char(string='Asset Number', tracking=True)
    category_id = fields.Many2one('itsm.category', string='Category', tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    purchase_date = fields.Date('Purchase Date', tracking=True)
    state = fields.Selection([
        ('in_use', 'In Use'),
        ('available', 'Available'),
        ('repair', 'Repair'),
        ('borrowed', 'Borrowed'),
    ], string='Status', tracking=True)
    employee_id = fields.Many2one('itsm.employee', string='Used by', tracking=True)
    division_id = fields.Many2one('itsm.division', string='Division', tracking=True)
    specification = fields.Text('Specification', tracking=True)
    activation_number = fields.Char(string='Activation Number', tracking=True)
    system_model = fields.Char('System Model', tracking=True)
    brand_id = fields.Many2one('itsm.brands', string='Brand', tracking=True)
    location_id = fields.Many2one('itsm.location', string='Location', tracking=True)
    ram = fields.Selection([
        ('4gb', '4GB'),
        ('8gb', '8GB'),
        ('12gb', '12GB'),
        ('16gb', '16GB'),
        ('24gb', '24GB'),
        ('32gb', '32GB'),
        ('64gb', '64GB'),
    ], string='RAM', tracking=True)
    storage_type = fields.Selection([
            ('ssd', 'SSD'),
            ('hdd', 'HDD'),
        ], string='Storage Type', tracking=True)
    storage_size = fields.Selection([
        ('128gb', '128GB'),
        ('256gb', '256GB'),
        ('512gb', '512GB'),
        ('1tb', '1TB'),
        ('2tb', '2TB'),
        ('4tb', '4TB'),
        ('6tb', '6TB'),
        ('8tb', '8TB'),
    ], string='Storage Size', tracking=True)
    antivirus = fields.Boolean('Antivirus', tracking=True)
    antivirus_brand = fields.Text('Antivirus Brands', tracking=True)
    charger = fields.Boolean('Charger', tracking=True)
    mouse = fields.Boolean('Mouse', tracking=True)
    keyboard = fields.Boolean('Keyboard', tracking=True)
    notes = fields.Text('Notes', tracking=True)
    #maintenance_ids = fields.One2many('itsm.maintenance', 'asset_id', string='Maintenance', readonly=True)
    #credential_ids = fields.One2many('itsm.credential', 'asset_id', string='Credentials', readonly=True)
    #used_id = fields.Many2one(string='Used By', related='assign_ids.new_employee_id', readonly=True)
    #location_id = fields.Many2one(string='Location', related='assign_ids.new_location_id', store=True, readonly=True)

    has_ups = fields.Boolean(string="UPS", default=False, tracking=True)
    ups_asset_id = fields.Many2one("itsm.asset", string="UPS Number", tracking=True, domain="[('category_id.name', '=', 'UPS'),('pc_asset_ids', '=', False)]")
    pc_asset_ids = fields.One2many("itsm.asset", "ups_asset_id", string="Used By PC", readonly=True)
    is_pc = fields.Boolean(string="Is PC", compute="_compute_is_pc")
    is_ups = fields.Boolean(string="Is UPS", compute="_compute_is_ups")

    lisence_id = fields.Many2one("itsm.lisence", string="License", tracking=True)
    antivirus_license_id = fields.Many2one("itsm.lisence", string="Antivirus Software", tracking=True, domain="[('category_id.name', '=', 'Antivirus'), ('available_stock', '>', 0)]",)
    asset_image = fields.Image(string="Picture", max_width=1280, max_height=1280, tracking=False)

    @api.onchange("antivirus")
    def _onchange_antivirus(self):
        if not self.antivirus:
            self.antivirus_license_id = False

    @api.constrains("antivirus", "antivirus_license_id")
    def _check_antivirus_license_stock(self):
        for record in self:

            if not record.antivirus and record.antivirus_license_id:
                raise ValidationError(
                    "Antivirus Software harus dikosongkan "
                    "jika Antivirus tidak dicentang."
                )

            if record.antivirus and record.antivirus_license_id:

                license_record = record.antivirus_license_id

                assigned_count = self.search_count([
                    ("antivirus_license_id", "=", license_record.id),
                    ("id", "!=", record.id),
                ])

                if assigned_count >= license_record.stock:
                    raise ValidationError(
                        "License '%s' sudah mencapai batas stock.\n\n"
                        "Stock      : %s\n"
                        "Assigned   : %s\n"
                        "Available  : 0\n\n"
                        "Tidak dapat assign license ini ke asset lain."
                        % (
                            license_record.name,
                            license_record.stock,
                            assigned_count,
                        )
                    )

    @api.depends("category_id")
    def _compute_is_pc(self):
        for record in self:
            record.is_pc = record.category_id.name == "PC"

    @api.depends("category_id")
    def _compute_is_ups(self):
        for record in self:
            record.is_ups = record.category_id.name == "UPS"

    @api.onchange("category_id")
    def _onchange_category_id(self):
        if self.category_id.name != "PC":
            self.has_ups = False
            self.ups_asset_id = False

    @api.constrains("ups_asset_id")
    def _check_ups_assignment(self):
        for record in self:
            if record.ups_asset_id:
                other_pcs = self.search([
                    ("ups_asset_id", "=", record.ups_asset_id.id),
                    ("id", "!=", record.id),
                ])

                if other_pcs:
                    raise ValidationError(
                        "UPS %s sudah digunakan oleh PC %s."
                        % (
                            record.ups_asset_id.name,
                            ", ".join(other_pcs.mapped("name")),
                        )
                    )

    
    
    def copy(self, default=None):
        default = dict(default or {})

        default["name"] = self.env["ir.sequence"].next_by_code(
            "itsm.asset"
        ) or "/"

        return super().copy(default)
    
    @api.constrains("name")
    def _check_unique_name(self):
        for rec in self:
            if not rec.name:
                continue

            duplicate = self.search([
                ("id", "!=", rec.id),
                ("name", "=", rec.name),
            ], limit=1)

            if duplicate:
                raise ValidationError("Asset Number already exists!")


    def action_generate_asset_label(self):
        if not self:
            return False

        # ==========================================================
        # CREATE EXCEL IN MEMORY
        # ==========================================================

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(
            output,
            {
                'in_memory': True,
            }
        )

        worksheet = workbook.add_worksheet(
            'Asset Labels'
        )

        # ==========================================================
        # PAGE SETUP
        # ==========================================================

        worksheet.set_landscape()
        worksheet.set_paper(9)  # A4

        worksheet.fit_to_pages(1, 0)

        worksheet.set_margins(
            left=0.20,
            right=0.20,
            top=0.25,
            bottom=0.25,
        )

        worksheet.center_horizontally()

        # ==========================================================
        # COLUMN WIDTH
        #
        # LABEL 1 : A:F
        # GAP     : G
        # LABEL 2 : H:M
        # GAP     : N
        # LABEL 3 : O:T
        # ==========================================================

        # Label 1
        worksheet.set_column('A:A', 3)
        worksheet.set_column('B:B', 3)
        worksheet.set_column('C:C', 3)
        worksheet.set_column('D:D', 3)
        worksheet.set_column('E:E', 3)
        worksheet.set_column('F:F', 3)

        # Gap
        worksheet.set_column('G:G', 2)

        # Label 2
        worksheet.set_column('H:H', 3)
        worksheet.set_column('I:I', 3)
        worksheet.set_column('J:J', 3)
        worksheet.set_column('K:K', 3)
        worksheet.set_column('L:L', 3)
        worksheet.set_column('M:M', 3)

        # Gap
        worksheet.set_column('N:N', 2)

        # Label 3
        worksheet.set_column('O:O', 3)
        worksheet.set_column('P:P', 3)
        worksheet.set_column('Q:Q', 3)
        worksheet.set_column('R:R', 3)
        worksheet.set_column('S:S', 3)
        worksheet.set_column('T:T', 3)

        # ==========================================================
        # FORMAT
        # ==========================================================

        company_logo = self.env.company.logo
        logo_image = None

        if company_logo:
            logo_image = io.BytesIO(
                base64.b64decode(company_logo)
            )

        logo_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 8,
            'border': 1,
            'border_color': '#000000',
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 7,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1,
            'border_color': '#000000',
        })

        asset_number_format = workbook.add_format({
            'bold': True,
            'font_size': 5,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        month_format = workbook.add_format({
            'bold': True,
            'font_size': 5,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        year_format = workbook.add_format({
            'bold': True,
            'font_size': 5,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        company_format = workbook.add_format({
            'bold': True,
            'font_size': 7,
            'align': 'center',
            'valign': 'vcenter',
        })

        company_border_format = workbook.add_format({
            'bold': True,
            'font_size': 7,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        # ==========================================================
        # GENERATE LABEL
        #
        # 3 HORIZONTAL × 5 VERTICAL
        # 15 LABEL / PAGE
        # ==========================================================

        for index, asset in enumerate(self):

            page_index = index // 15
            position = index % 15

            label_row = position // 3
            label_col = position % 3

            # ------------------------------------------------------
            # COLUMN POSITION
            #
            # Label 1 = A:F
            # Label 2 = H:M
            # Label 3 = O:T
            # ------------------------------------------------------

            start_col = label_col * 7
            end_col = start_col + 5

            # ------------------------------------------------------
            # ROW POSITION
            #
            # 4 rows per label
            # 2 rows gap between label groups
            # ------------------------------------------------------

            start_row = (
                page_index * 22
                + label_row * 4
            )

            row_1 = start_row
            row_2 = start_row + 1
            row_3 = start_row + 2
            row_4 = start_row + 3

            # ======================================================
            # ROW HEIGHT
            # ======================================================

            worksheet.set_row(row_1, 10)
            worksheet.set_row(row_2, 10)
            worksheet.set_row(row_3, 10)
            worksheet.set_row(row_4, 18)

            # ======================================================
            # ASSET DATA
            # ======================================================

            title = asset.specification or ''

            asset_number = asset.name or ''

            # ======================================================
            # DATE
            # ======================================================

            month = ''
            year = ''

            if asset.purchase_date:
                month = asset.purchase_date.strftime('%b').upper()
                year = asset.purchase_date.strftime('%Y')

            # ======================================================
            # LOGO
            #
            # A:B
            # ======================================================

            worksheet.merge_range(
                row_1,
                start_col,
                row_2,
                start_col,
                '',
                logo_format,
            )

            company_logo = self.env.company.logo

            if company_logo:

                logo_image = io.BytesIO(
                    base64.b64decode(company_logo)
                )

                worksheet.insert_image(
                    row_1,
                    start_col,
                    'company_logo.png',
                    {
                        'image_data': logo_image,

                        'x_scale': 0.04,
                        'y_scale': 0.04,

                        'x_offset': 3,
                        'y_offset': 4,

                        'object_position': 1,
                    }
                )

            # ======================================================
            # TITLE
            #
            # C:F
            # ======================================================

            worksheet.merge_range(
                row_1,
                start_col + 1,
                row_1,
                end_col,
                title,
                title_format,
            )

            # ======================================================
            # ASSET NUMBER
            #
            # C:D
            # ======================================================

            worksheet.merge_range(
                row_2,
                start_col + 1,
                row_2,
                start_col + 3,
                asset_number,
                asset_number_format,
            )

            # ======================================================
            # MONTH
            #
            # E
            # ======================================================

            worksheet.write(
                row_2,
                start_col + 4,
                month,
                month_format,
            )

            # ======================================================
            # YEAR
            #
            # F
            # ======================================================

            worksheet.write(
                row_2,
                start_col + 5,
                year,
                year_format,
            )

            # ======================================================
            # COMPANY
            #
            # A:F
            # ======================================================

            worksheet.merge_range(
                row_3,
                start_col,
                row_3,
                end_col,
                'PT. PORT AVANT LOGISTICS',
                company_border_format,
            )

            # ======================================================
            # EMPTY ROW
            # ======================================================

            worksheet.merge_range(
                row_4,
                start_col,
                row_4,
                end_col,
                '',
                company_format,
            )

        # ==========================================================
        # PRINT AREA
        # ==========================================================

        total_pages = (len(self) + 14) // 15

        total_rows = total_pages * 22

        worksheet.print_area(
            0,
            0,
            total_rows - 1,
            19,
        )

        # ==========================================================
        # PAGE BREAKS
        # ==========================================================

        page_breaks = []

        for page in range(1, total_pages):
            page_breaks.append(page * 22)

        if page_breaks:
            worksheet.set_h_pagebreaks(page_breaks)

        # ==========================================================
        # CLOSE WORKBOOK
        # ==========================================================

        workbook.close()

        output.seek(0)

        file_data = output.read()

        output.close()

        # ==========================================================
        # CREATE ATTACHMENT
        # ==========================================================

        attachment = self.env['ir.attachment'].create({
            'name': 'Asset_Labels.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'mimetype': (
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            ),
            'res_model': 'itsm.asset',
            'res_id': self[0].id,
        })

        # ==========================================================
        # DOWNLOAD
        # ==========================================================

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }