import xlrd
import logging
import datetime
import re

from management.models import Massage, StaffInfo, ServiceMenu
from management.views import related_to_customerinfo

wb = xlrd.open_workbook("/data/kali/test1.xls")
tb = wb.sheet_by_index(0)
loger = logging.getLogger('runlog')
staff_list = StaffInfo.objects.values_list('name', flat=True)


def read_date(table, r, c):
    """读取日期"""
    cell_tp = table.cell(r, c).ctype
    cell_vl = table.cell(r, c).value
    loger.debug('读取表格时间字段，第{}行 第{}列 value={}, 类型ctype={}'.format(r, c, cell_vl, cell_tp))
    if cell_tp == 3:
        cell_date = xlrd.xldate_as_datetime(cell_vl, 0).date()
        return cell_date
    elif cell_tp == 1:
        loger.warning('读取表格时间字段，第{}行 第{}列类型为 String, value={}， 尝试转换为date'.format(r, c, cell_vl))
        try:
            cell_date = datetime.datetime.strptime(cell_vl, '%Y-%m-%d').date()
            return cell_date
        except ValueError:
            return None
    else:
        loger.error('读取表格时间字段，第{}行 第{}列, 无效内容'.format(r, c))
        return None


def check_date(the_date, s_date, e_date):
    """the_date 为None情况判断, 时间不满足True，其余情况False"""
    if the_date:  # the_date ！= None
        if s_date < the_date < e_date:
            return False
        else:
            return True
    return False


def rbk(string):
    """remove_blank"""
    return re.sub(' +', ' ', string).strip()


def ttp(string):
    """auto related To service_TyPe"""
    the_name = string.split('-')[0].strip()
    menu_name_set = ServiceMenu.objects.filter(items=the_name)
    if menu_name_set.__len__() == 1:
        return menu_name_set[0].pk
    elif menu_name_set.__len__() > 1:
        try:
            the_duration = int(string.split('-')[1].strip())
            menu_name_set = menu_name_set.filter(duration=the_duration)
            return menu_name_set[0].pk
        except:
            return None


def tmg(string):
    """related To MassaGist"""
    slist = StaffInfo.objects.filter(name=string)
    try:
        return slist[0].pk
    except:
        return None


def read_number(ss):
    """指定数字类型"""
    try:
        return int(ss)
    except ValueError:
        return 0


def main_read(table, timelimit=False, s_date=datetime.date.today(), e_date=datetime.date.today()):
    table = tb
    end_row_num = table.nrows - 1
    if table.cell(2, 0).value.lower() != 'name':
        loger.error('表格不符合模板规范， 第3行，第1列非NAME标题栏')
        return {'result': False}
    else:
        start_row_num = 3
    # 读取标题栏，方便定位
    title_list = table.row_values(start_row_num - 1)
    loger.debug('表格标题栏：{}'.format(title_list))
    # 批量导入
    mlist = []
    for r_num in range(start_row_num, end_row_num):
        l = table.row_values(r_num)
        the_date = read_date(table, r_num, 5)
        # 指定导入时间条件， 时间条件不满足不导入该条数据
        if timelimit and check_date(the_date, s_date, e_date):
            continue
        name, phone, address = rbk(l[0]), rbk(l[1]), rbk(l[2])
        service_type_id, massagist_id = ttp(rbk(l[3]).upper()), tmg(rbk(l[6].lower()))
        amount, fee = read_number(l[4]), read_number(l[7])
        m1 = Massage(name=name, phone=phone, address=address, service_date=the_date, fee=fee,
                     amount=amount, massagist_id=massagist_id, service_type_id=service_type_id, )
        m1 = related_to_customerinfo(m1)
        mlist.append(m1)
    loger.info('读取Excel 完成，开始插入Database')
    Massage.objects.bulk_create(mlist)
