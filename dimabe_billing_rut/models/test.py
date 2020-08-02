if (contract.type_id.name == 'Sueldo Empresarial') and (
        contract.wage >= round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)):
    result = round(payslip.indicadores_id.tope_imponible_afp * payslip.indicadores_id.uf)
elif (contract.type_id.name == 'Sueldo Empresarial'):
    result = contract.wage
else:
    if payslip.have_absence:
        if payslip.vacation_days > 0:
        result =  round(
            (contract.wage / 30) * (worked_days.WORK100.number_of_days - payslip.absence_days))
    else:
        result = round(
            (contract.wage / 30) * (worked_days.WORK100.number_of_days))