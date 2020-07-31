if (contract.type_id.name == 'Sueldo Empresarial') and (
        contract.wage >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)):
    result = round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)
elif (contract.type_id.name == 'Sueldo Empresarial'):
    result = contract.wage
else:
    if worked_days.filtered(lambda a: a.unpaid == True):
        result = round(
            (contract.wage / 30) * (worked_days.WORK100.number_of_days - worked_days.PRM130.number_of_days))
    else:
        result = result = round((contract.wage / 30) * (worked_days.WORK100.number_of_days))
