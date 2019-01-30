import xlrd
import logging
import datetime
import re

from management.models import Massage, StaffInfo, ServiceMenu, CustomerInfo
from .query_unit import related_to_customerinfo

# wb = xlrd.open_workbook("/data/kali/test1.xls")
# tb = wb.sheet_by_index(0)
loger = logging.getLogger('runlog')
staff_list = StaffInfo.objects.values_list('name', flat=True)


def read_date(table, r, c):
    """读取日期"""
    cell_tp = table.cell(r, c).ctype
    cell_vl = table.cell(r, c).value
    loger.debug('读取表格时间字段，第{}行 第{}列 value={}, 类型ctype={}'.format(r + 1, c + 1, cell_vl, cell_tp))
    if cell_tp == 3:
        cell_date = xlrd.xldate_as_datetime(cell_vl, 0).date()
        return cell_date
    elif cell_tp == 1:
        loger.warning('读取表格时间字段，第{}行 第{}列类型为 String, value={}， 尝试转换为date'.format(r + 1, c + 1, cell_vl))
        try:
            cell_date = datetime.datetime.strptime(cell_vl, '%Y-%m-%d').date()
            return cell_date
        except ValueError:
            return datetime.date(2017, 1, 1)
    else:
        loger.error('读取表格时间字段，第{}行 第{}列, 无效内容'.format(r + 1, c + 1))
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


def main_read(table, timelimit='0', s_date=datetime.date.today(), e_date=datetime.date.today()):
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
        line = table.row_values(r_num)
        the_date = read_date(table, r_num, 5)
        # 指定导入时间条件， 时间条件不满足不导入该条数据
        if timelimit == '1' and check_date(the_date, s_date, e_date):
            continue
        name, phone, address = rbk(line[0]), rbk(line[1]), rbk(line[2])
        loger.debug(
            'function main_read读取Excel第{}行 name={}, phone={}, address={}'.format(r_num + 1, name, phone, address))
        service_type_id, massagist_id = ttp(rbk(line[3]).upper()), tmg(rbk(line[6].lower()))
        loger.debug(
            'function main_read读取Excel第{}行 service_type_id={}, massagist_id={}, '.format(r_num + 1, service_type_id,
                                                                                         massagist_id))
        amount, fee = read_number(line[4]), read_number(line[7])
        note = ''
        loger.debug(
            'function main_read读取Excel第{}行 amount={}, fee={}, '.format(r_num + 1, amount, fee))
        if not service_type_id:
            note = note + ' , ' + str(rbk(line[3]).upper())
        if not massagist_id:
            note = note + ' , ' + str(rbk(line[6].lower()))
        m1 = Massage(name=name, phone=phone, address=address, service_date=the_date, fee=fee, amount=amount,
                     massagist_id=massagist_id, service_type_id=service_type_id, note=note)
        m1 = related_to_customerinfo(m1)
        mlist.append(m1)
        loger.debug('function main_read读取Excel第{}行完成'.format(r_num + 1))
    loger.info('读取Excel 完成， 获取数据{} 行'.format(len(mlist)))
    loger.debug('读取Excel 数据详情：\n {}'.format(str(mlist)))
    return mlist


def data_insert(the_list):
    try:
        Massage.objects.bulk_create(the_list)
        number_of_data = len(the_list)
        loger.debug('Massage 导入数据成功， 读取数据{0}条，导入成功{0}条'.format(number_of_data))
        return {'status': 1, 'num': number_of_data}
    except Exception as e:
        loger.error('Massage 导入数据失败，the_list={}'.format(the_list))
        return {'status': 0, 'error': str(e)}
