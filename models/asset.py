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
        ('damaged', 'Damaged'),
        ('disposal', 'Disposal'),
        ('sold', 'Sold'),
    ], string='Status', tracking=True)
    employee_id = fields.Many2one('itsm.employee', string='Used by', tracking=True)
    division_id = fields.Many2one('itsm.division', string='Division', tracking=True)
    specification = fields.Text('Specification', tracking=True)
    activation_number = fields.Char(string='Activation Number', tracking=True)
    system_model = fields.Char('System Model', tracking=True)
    brand_id = fields.Many2one('itsm.brands', string='Brand', tracking=True)
    location_id = fields.Many2one('itsm.location', string='Location', tracking=True)
    company_id = fields.Many2one('itsm.company', string='Company', tracking=True)
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
    asset_label_generated = fields.Boolean(string='Label Generated', default=False, tracking=True)


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

        asset_names = self.mapped('name')

        # ==========================================================
        # CHECK ASSET LABEL ALREADY GENERATED
        # ==========================================================

        already_generated = self.filtered(
            lambda asset: asset.asset_label_generated
        )

        if already_generated:
            asset_numbers = already_generated.mapped('name')

            asset_list = "\n".join(
                "• %s" % (name or "Asset number not found")
                for name in asset_numbers
            )

            raise ValidationError(
                "This asset already generated:\n\n"
                "%s\n\n"
                "Please uncheck 'Label Generated' for re-generate"
                % asset_list
            )

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
        # ==========================================================

        for index, asset in enumerate(self):

            page_index = index // 45
            position = index % 45

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
                page_index * 62
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

            worksheet.merge_range(row_1,start_col,row_2,start_col,'',logo_format)

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
            # C:F
            # ======================================================

            worksheet.merge_range(row_1,start_col + 1,row_1,end_col,title,title_format)

            # ======================================================
            # ASSET NUMBER
            # C:D
            # ======================================================

            worksheet.merge_range(row_2,start_col + 1,row_2,start_col + 3,asset_number,asset_number_format)

            # ======================================================
            # MONTH
            # E
            # ======================================================

            worksheet.write(row_2,start_col + 4,month,month_format)

            # ======================================================
            # YEAR
            # F
            # ======================================================

            worksheet.write(row_2,start_col + 5,year,year_format)

            # ======================================================
            # COMPANY
            # A:F
            # ======================================================

            worksheet.merge_range(row_3,start_col,row_3,end_col,'PT. PORT AVANT LOGISTICS',company_border_format)

            # ======================================================
            # EMPTY ROW
            # ======================================================

            worksheet.merge_range(row_4,start_col,row_4,end_col,'',company_format)

        # ==========================================================
        # PRINT AREA
        # ==========================================================

        total_pages = (len(self) + 44) // 45
        total_rows = total_pages * 62
        worksheet.print_area(0,0,total_rows - 1,19)

        # ==========================================================
        # PAGE BREAKS
        # ==========================================================

        page_breaks = []
        for page in range(1, total_pages):
            page_breaks.append(page * 62)
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
        # MARK LABEL AS GENERATED
        # ==========================================================

        self.write({
            'asset_label_generated': True,
        })

        # ==========================================================
        # LOG GENERATE ASSET LABEL
        # ==========================================================

        generated_time = fields.Datetime.now()

        for asset in self:
            asset.message_post(
                body=(
                    "Label Generated Successfully"
                    "Date/Time: %s"
                    "Generated By: %s"
                    % (
                        fields.Datetime.context_timestamp(
                            asset,
                            generated_time
                        ).strftime('%d/%m/%Y %H:%M:%S'),
                        self.env.user.name,
                    )
                ),
                subtype_xmlid='mail.mt_note',
            )

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


    def action_generate_asset_excel(self):
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

        worksheet = workbook.add_worksheet('Assets')

        # ==========================================================
        # FORMAT
        # ==========================================================

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'border_color': '#000000',
        })

        header_format = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1,
            'border_color': '#000000',
            'bg_color': '#D9EAF7',
        })

        text_format = workbook.add_format({
            'font_size': 9,
            'valign': 'top',
            'text_wrap': True,
            'border': 1,
            'border_color': '#000000',
        })

        center_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'border': 1,
            'border_color': '#000000',
        })

        date_format = workbook.add_format({
            'font_size': 9,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'dd/mm/yyyy',
            'border': 1,
            'border_color': '#000000',
        })

        # ==========================================================
        # COLUMN DEFINITION
        # ==========================================================

        columns = [
            ('Asset Number', 'name'),
            ('Category', 'category_id'),
            ('Serial Number', 'serial_number'),
            ('Purchase Date', 'purchase_date'),
            ('Status', 'state'),
            ('Used by', 'employee_id'),
            ('Division', 'division_id'),
            ('Specification', 'specification'),
            ('Activation Number', 'activation_number'),
            ('System Model', 'system_model'),
            ('Brand', 'brand_id'),
            ('Location', 'location_id'),
            ('RAM', 'ram'),
            ('Storage Type', 'storage_type'),
            ('Storage Size', 'storage_size'),
            ('Antivirus', 'antivirus'),
            ('Antivirus Brands', 'antivirus_brand'),
            ('Charger', 'charger'),
            ('Mouse', 'mouse'),
            ('Keyboard', 'keyboard'),
            ('Notes', 'notes'),
            ('UPS', 'has_ups'),
            ('UPS Number', 'ups_asset_id'),
            ('Used By PC', 'pc_asset_ids'),
            ('Is PC', 'is_pc'),
            ('Is UPS', 'is_ups'),
            ('License', 'lisence_id'),
            ('Antivirus Software', 'antivirus_license_id'),
            ('Picture', 'asset_image'),
        ]

        # ==========================================================
        # TITLE
        # ==========================================================

        total_columns = len(columns)
        worksheet.merge_range(
            0,
            0,
            0,
            total_columns - 1,
            'ASSET LIST',
            title_format,
        )

        worksheet.set_row(0, 25)

        # ==========================================================
        # HEADER
        # ==========================================================

        header_row = 2

        for col, (label, field_name) in enumerate(columns):
            worksheet.write(
                header_row,
                col,
                label,
                header_format,
            )

        worksheet.set_row(header_row, 30)

        # ==========================================================
        # SELECTION LABELS
        # ==========================================================

        state_selection = dict(
            self._fields['state'].selection
        )

        ram_selection = dict(
            self._fields['ram'].selection
        )

        storage_type_selection = dict(
            self._fields['storage_type'].selection
        )

        storage_size_selection = dict(
            self._fields['storage_size'].selection
        )

        # ==========================================================
        # WRITE ASSET DATA
        # ==========================================================

        for row, asset in enumerate(
            self,
            start=header_row + 1
        ):

            # ------------------------------------------------------
            # ASSET NUMBER
            # ------------------------------------------------------

            worksheet.write(row,0,asset.name or '',text_format)

            # ------------------------------------------------------
            # CATEGORY
            # ------------------------------------------------------

            worksheet.write(row,1,asset.category_id.display_name if asset.category_id else '',text_format)

            # ------------------------------------------------------
            # SERIAL NUMBER
            # ------------------------------------------------------

            worksheet.write(row,2,asset.serial_number or '',text_format)

            # ------------------------------------------------------
            # PURCHASE DATE
            # ------------------------------------------------------

            if asset.purchase_date:
                purchase_date = fields.Date.from_string(
                    asset.purchase_date
                )

                worksheet.write_datetime(
                    row,
                    3,
                    purchase_date,
                    date_format,
                )
            else:
                worksheet.write(
                    row,
                    3,
                    '',
                    date_format,
                )

            # ------------------------------------------------------
            # STATUS
            # ------------------------------------------------------

            worksheet.write(row,4,state_selection.get(asset.state,'') if asset.state else '',center_format)

            # ------------------------------------------------------
            # USED BY
            # ------------------------------------------------------

            worksheet.write(row,5,asset.employee_id.display_name if asset.employee_id else '', text_format)

            # ------------------------------------------------------
            # DIVISION
            # ------------------------------------------------------

            worksheet.write(row,6,asset.division_id.display_name if asset.division_id else '', text_format)

            # ------------------------------------------------------
            # SPECIFICATION
            # ------------------------------------------------------

            worksheet.write(row, 7, asset.specification or '', text_format)

            # ------------------------------------------------------
            # ACTIVATION NUMBER
            # ------------------------------------------------------

            worksheet.write(row,8,asset.activation_number or '',text_format)

            # ------------------------------------------------------
            # SYSTEM MODEL
            # ------------------------------------------------------

            worksheet.write(row,9,asset.system_model or '', text_format)

            # ------------------------------------------------------
            # BRAND
            # ------------------------------------------------------

            worksheet.write(row,10, asset.brand_id.display_name if asset.brand_id else '', text_format)

            # ------------------------------------------------------
            # LOCATION
            # ------------------------------------------------------

            worksheet.write(row,11,asset.location_id.display_name if asset.location_id else '', text_format)

            # ------------------------------------------------------
            # RAM
            # ------------------------------------------------------

            worksheet.write(row,12,ram_selection.get(asset.ram,'') if asset.ram else '',center_format)

            # ------------------------------------------------------
            # STORAGE TYPE
            # ------------------------------------------------------

            worksheet.write(row,13,storage_type_selection.get(asset.storage_type,'') if asset.storage_type else '',center_format)

            # ------------------------------------------------------
            # STORAGE SIZE
            # ------------------------------------------------------

            worksheet.write(row,14,storage_size_selection.get(asset.storage_size,'') if asset.storage_size else '',center_format)

            # ------------------------------------------------------
            # ANTIVIRUS
            # ------------------------------------------------------

            worksheet.write(row,15,'Yes' if asset.antivirus else 'No',center_format)

            # ------------------------------------------------------
            # ANTIVIRUS BRANDS
            # ------------------------------------------------------

            worksheet.write(row,16,asset.antivirus_brand or '',text_format)

            # ------------------------------------------------------
            # CHARGER
            # ------------------------------------------------------

            worksheet.write(row,17,'Yes' if asset.charger else 'No',center_format)

            # ------------------------------------------------------
            # MOUSE
            # ------------------------------------------------------

            worksheet.write(row,18,'Yes' if asset.mouse else 'No',center_format)

            # ------------------------------------------------------
            # KEYBOARD
            # ------------------------------------------------------

            worksheet.write(row,19,'Yes' if asset.keyboard else 'No',center_format)

            # ------------------------------------------------------
            # NOTES
            # ------------------------------------------------------

            worksheet.write(row,20,asset.notes or '',text_format,)

            # ------------------------------------------------------
            # UPS
            # ------------------------------------------------------

            worksheet.write(row,21,'Yes' if asset.has_ups else 'No',center_format)

            # ------------------------------------------------------
            # UPS NUMBER
            # ------------------------------------------------------

            worksheet.write(row,22,asset.ups_asset_id.display_name if asset.ups_asset_id else '',text_format,)

            # ------------------------------------------------------
            # USED BY PC
            # ------------------------------------------------------

            pc_names = ', '.join(asset.pc_asset_ids.mapped('name'))
            worksheet.write(row,23, pc_names,text_format)

            # ------------------------------------------------------
            # IS PC
            # ------------------------------------------------------

            worksheet.write(row, 24, 'Yes' if asset.is_pc else 'No', center_format)

            # ------------------------------------------------------
            # IS UPS
            # ------------------------------------------------------

            worksheet.write(row, 25, 'Yes' if asset.is_ups else 'No',center_format)

            # ------------------------------------------------------
            # LICENSE
            # ------------------------------------------------------

            worksheet.write(row, 26, asset.lisence_id.display_name if asset.lisence_id else '',text_format)
            
            # ------------------------------------------------------
            # ANTIVIRUS SOFTWARE
            # ------------------------------------------------------

            worksheet.write(row,27,asset.antivirus_license_id.display_name if asset.antivirus_license_id else '', text_format)

            # ------------------------------------------------------
            # PICTURE
            # ------------------------------------------------------

            worksheet.write(row,28,'Yes' if asset.asset_image else 'No',center_format)
            worksheet.set_row(row, 45,)

        # ==========================================================
        # COLUMN WIDTH
        # ==========================================================

        widths = [
            18,  # Asset Number
            18,  # Category
            20,  # Serial Number
            14,  # Purchase Date
            14,  # Status
            22,  # Used by
            20,  # Division
            35,  # Specification
            22,  # Activation Number
            22,  # System Model
            18,  # Brand
            22,  # Location
            12,  # RAM
            15,  # Storage Type
            15,  # Storage Size
            12,  # Antivirus
            25,  # Antivirus Brands
            12,  # Charger
            12,  # Mouse
            12,  # Keyboard
            30,  # Notes
            10,  # UPS
            18,  # UPS Number
            25,  # Used By PC
            10,  # Is PC
            10,  # Is UPS
            22,  # License
            25,  # Antivirus Software
            12,  # Picture
        ]

        for col, width in enumerate(widths):
            worksheet.set_column(
                col,
                col,
                width,
            )

        # ==========================================================
        # FREEZE HEADER
        # ==========================================================

        worksheet.freeze_panes(
            header_row + 1,
            0,
        )

        # ==========================================================
        # FILTER
        # ==========================================================

        worksheet.autofilter(
            header_row,
            0,
            header_row + len(self),
            total_columns - 1,
        )

        # ==========================================================
        # PAGE SETUP
        # ==========================================================

        worksheet.set_landscape()
        worksheet.set_paper(9)

        worksheet.set_margins(
            left=0.25,
            right=0.25,
            top=0.50,
            bottom=0.50,
        )

        worksheet.fit_to_pages(
            1,
            0,
        )

        worksheet.repeat_rows(
            header_row,
            header_row,
        )

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
            'name': 'Asset_List.xlsx',
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