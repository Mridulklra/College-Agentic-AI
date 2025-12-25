# Create demo_assignment_generator.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_demo_assignment():
    c = canvas.Canvas("demo_assignment.pdf", pagesize=letter)
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 750, "Data Structures Assignment")
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, "Subject: Data Structures and Algorithms")
    c.drawString(100, 700, "Due Date: As specified in email")
    
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 660, "Task:")
    
    c.setFont("Helvetica", 12)
    text = [
        "1. Implement a Linked List with insert, delete, and search operations",
        "2. Create a function to reverse the linked list",
        "3. Write test cases for all operations",
        "4. Document time complexity for each operation"
    ]
    
    y = 630
    for line in text:
        c.drawString(120, y, line)
        y -= 25
    
    c.save()
    print("✅ demo_assignment.pdf created!")

if __name__ == "__main__":
    create_demo_assignment()