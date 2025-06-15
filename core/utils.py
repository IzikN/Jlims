from core.models import TestAssignment
from core.models import AuditTrail
def save_audit(user, action, details=""):
    AuditTrail.objects.create(user=user, action=action, details=details)



def calculate_total_price(client):
    assignments = TestAssignment.objects.filter(sample__client=client)
    total = sum(assign.parameter.price for assign in assignments)
    return total
