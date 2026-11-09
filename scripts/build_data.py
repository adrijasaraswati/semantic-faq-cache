"""Rebuild the hand-authored synthetic corpus; no model-generated labels."""
import json
from pathlib import Path

ROWS = [
("refund_time", "How long does a refund take?", "Refunds arrive within 5–7 business days after the return is approved.", "When will I receive my refund?", "Refund kab milega?"),
("return_window", "What is the return window?", "Unused items can be returned within 30 days of delivery.", "How many days do I have to return a product?", "Return kitne din mein kar sakte hain?"),
("start_return", "How do I start a return?", "Open Orders, select the item, and choose Request return.", "How can I request a product return?", "Return request kaise shuru karun?"),
("cancel", "How can I cancel an order?", "Choose Cancel in Orders before the package is dispatched.", "How do I cancel my purchase before dispatch?", "Order cancel kaise karun?"),
("tracking", "How do I track my shipment?", "Open Orders and select Track shipment for the carrier link.", "Where can I see shipment tracking?", "Delivery tracking kahan dekhu?"),
("delivery_time", "How long does standard delivery take?", "Standard delivery takes 3–5 business days.", "What is the standard shipping time?", "Normal delivery kitne din leti hai?"),
("shipping_fee", "What is the shipping fee?", "Standard shipping costs ₹49; orders of ₹999 or more ship free.", "How much does shipping cost?", "Shipping ka charge kitna hai?"),
("cod", "Do you offer cash on delivery?", "Cash on delivery is available for eligible postal codes at checkout.", "Can I pay cash when the package arrives?", "Cash on delivery milti hai?"),
("payment", "Which payment methods are accepted?", "We accept UPI, debit cards, credit cards, and eligible cash on delivery.", "What ways can I pay?", "Payment ke kya options hain?"),
("failed_payment", "What if payment fails but money is deducted?", "Failed-payment deductions are reversed by the bank within 3–5 business days.", "My payment failed but the amount was debited; what happens?", "Payment fail hua par paise kat gaye?"),
("address_change", "Can I change the delivery address before dispatch?", "Edit the delivery address in Orders before dispatch.", "How do I edit a shipping address before shipment?", "Dispatch se pehle delivery address badal sakte hain?"),
("damaged", "What should I do if an item arrives damaged?", "Report damage through Orders within 48 hours and attach photos.", "How do I report a damaged product delivery?", "Item damaged aaya toh kya karun?"),
("wrong_item", "What if I receive the wrong item?", "Choose Wrong item in the return form for a free replacement.", "How do I replace an incorrectly delivered item?", "Galat item mila toh kya karein?"),
("exchange", "Can I exchange an item for another size?", "Unused clothing can be exchanged for another available size within 30 days.", "Are size exchanges available?", "Size exchange kar sakte hain?"),
("refund_method", "Which payment method is credited when a refund is issued?", "Prepaid refunds go to the original payment method; cash orders use a verified bank transfer.", "Which payment account receives a refund?", "Refund kis payment method mein aayega?"),
("return_fee", "Is return shipping free?", "Return pickup is free for damaged or incorrect items; other returns cost ₹49.", "Do I need to pay for return pickup?", "Return pickup ka charge lagta hai?"),
("international", "Do you ship internationally?", "We currently deliver only within India.", "Can you deliver outside India?", "India ke bahar delivery hoti hai?"),
("weekend", "Do you deliver on weekends?", "Weekend delivery depends on the local carrier's availability.", "Are Saturday and Sunday deliveries available?", "Weekend par delivery milti hai?"),
("coupon", "How do I apply a coupon?", "Enter the coupon code in the checkout discount field before paying.", "Where do I enter a discount code?", "Coupon code kahan lagau?"),
("stack_coupon", "Can I use multiple coupons on one order?", "Only one coupon can be applied per order.", "Can two discount codes be combined?", "Ek order pe do coupons laga sakte hain?"),
("invoice", "How can I download an invoice?", "Select Download invoice on the order details page.", "Where can I get my purchase invoice?", "Invoice download kaise karun?"),
("password", "How do I reset my password?", "Choose Forgot password on the sign-in page and follow the email link.", "How can I recover a forgotten password?", "Password bhool gaya reset kaise karun?"),
("delete_account", "How do I delete my account?", "Request account deletion from Settings, Privacy, Delete account.", "Where can I request account deletion?", "Account delete kaise karein?"),
("support", "How can I contact customer support?", "Use the chat on the Help page to reach the demo support team.", "Where can I reach the support team?", "Customer support se kaise baat karun?"),
("support_hours", "What are customer support hours?", "Demo support hours are 9 AM–6 PM IST, Monday through Saturday.", "When is the support team available?", "Support kitne baje khulta hai?"),
("stock", "How do I get notified when an item is back in stock?", "Select Notify me on the product page to subscribe to restock alerts.", "Can I subscribe to restock notifications?", "Stock wapas aaye toh notification kaise milega?"),
("warranty", "What warranty do electronics include?", "Electronics include the manufacturer's stated warranty shown on the product page.", "Where can I check an electronic product's warranty?", "Electronics ki warranty kahan dikhegi?"),
("gift_wrap", "Do you offer gift wrapping?", "Gift wrapping is available for eligible products at checkout for ₹30.", "Can my purchase be gift wrapped?", "Gift packing milti hai?"),
("loyalty", "How do loyalty points work?", "Earn one point per ₹100 spent; 10 points redeem for ₹10 at checkout.", "How are reward points earned and redeemed?", "Loyalty points kaise milte aur use hote hain?"),
("split_delivery", "Why are items in my order arriving separately?", "Items from different warehouses may ship in separate packages at no extra shipping cost.", "Why was my purchase split into separate shipments?", "Ek order ke items alag alag kyun aa rahe hain?")]

NONE = [
"I do not want a refund", "Refund nahi chahiye", "Do not cancel the order",
"Can I return a used mattress after two years?", "Will you refund cryptocurrency losses?",
"Can I cancel after the shipment has been delivered?", "Can I exchange food after eating it?",
"Can you deliver to Mars?", "What is tomorrow's weather?", "Who won the cricket match?",
"How do I bake a cake?", "Can you diagnose my headache?", "What stocks should I buy?",
"Write a poem about shopping", "Tell me a joke", "What is your CEO's salary?",
"Can I insure my car here?", "Do you provide home loans?", "Can you book a train ticket?",
"How do I renew my passport?", "Can you repair my laptop at home?", "Can you install an air conditioner?",
"Do you rent furniture?", "Can I sell my used phone to you?", "Can I pay with gold?",
"Do you offer a student subscription?", "Can you change the manufacturer's warranty terms?",
"Is there a lifetime free delivery subscription?", "Can you reserve inventory for six months?",
"Can you price match a foreign store?", "What is the carbon footprint of each warehouse?",
"Do you offer wholesale reseller contracts?", "Can I buy a franchise?", "Do you accept job applications?",
"Can you donate my loyalty points to charity?", "Is my bank account balance sufficient?",
"Where is order ID 123456 right now?", "My name is Anil; what is my refund status?",
"Mera loan approve kab hoga?", "Mera insurance premium kitna hai?"
]

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "data"
    root.mkdir(exist_ok=True)
    faqs = [dict(id=r[0], question=r[1], answer=r[2]) for r in ROWS]
    tests = [dict(id=f"q{i*2+j+1:03}",question=r[3+j],expected=r[0],language="en" if j==0 else "hinglish") for i,r in enumerate(ROWS) for j in range(2)]
    tests += [dict(id=f"q{i+61:03}",question=q,expected=None,language="mixed") for i,q in enumerate(NONE)]
    assert len(faqs)==30 and len(tests)==100
    for filename, value in [("faqs.json",faqs),("questions.json",tests)]:
        (root/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
