# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 15:53:23 2019

@author: nhern
"""

from LibTaca.TacaTools import WriteExcel
from LibTaca.TacaTools import AddExcel
import xlsxwriter

lista1 = [1,2,3,4,5]
lista2 = [6,7,8,9,0]

book = WriteExcel('TestExcel',[],0)
AddExcel(book,lista1,1)


workbook = xlsxwriter.Workbook('TestExcel2.xls')
worksheet = workbook.add_worksheet()
for i,item in enumerate(lista1):
    worksheet.write(i, 0, item)
    
workbook.close()

workbook = xlsxwriter.Workbook('TestExcel2.xls')
worksheet = workbook.add_worksheet()
for i,item in enumerate(lista2):
    worksheet.write(i, 1, item)

workbook.close()