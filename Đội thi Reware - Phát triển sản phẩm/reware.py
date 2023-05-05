import firebase_admin
import threading
from firebase_admin import firestore
import gpiozero
from time import sleep
import time
import threading

class Slot:
    def __init__(self, firebase_id, lock_pin, echo_pin, trig_pin, ir_pin, threshold):
        self.firebase_id = firebase_id
        self.lock_pin = lock_pin
        self.echo_pin = echo_pin
        self.trig_pin = trig_pin
        self.ir_pin = ir_pin
        self.threshold = threshold

        self.db_ref = db.collection(u'slot_info').document(firebase_id)
        
        self.lock = gpiozero.DigitalOutputDevice(lock_pin)
        self.lock.on()

        self.ultrasonic = gpiozero.DistanceSensor(echo_pin, trig_pin)
        if ir_pin != -1:
            self.ir = gpiozero.LineSensor(ir_pin)
        
    def UpdateCapacity(self):
        if self.ultrasonic.distance * 100 <= self.threshold:
            is_empty = False
        else:
            is_empty = True
        new_info = {'current_capacity': self.ultrasonic.distance * 100, 'is_empty': is_empty}
        print(new_info)
        self.db_ref.update(new_info)

    def UpdateIsOpen(self, is_open):
        self.db_ref.update({'is_open': is_open})

def open_lock(lock_slot):
    print(f'Opening lock at {lock_slot.lock.pin}')
    lock_slot.lock.off()
    sleep(5)
    lock_slot.lock.on()
    lock_slot.UpdateIsOpen(False)

cred_obj = firebase_admin.credentials.Certificate('./key.json')
default_app = firebase_admin.initialize_app(cred_obj)

db = firestore.client(default_app)

slots = {}
slots['D1'] = Slot('iftRzDkFlceavS9hZUnK', 14, 27, 17, -1, 28)
slots['L2'] = Slot('NT0C6e0kcrYKU3ekUBGC', 18, 24, 23, -1, 21)
slots['KHAC'] = Slot('v86nZgw9ceSUgdAcjyS9', 15, 20, 21, -1, 2)

event_done = threading.Event()

def on_snapshot(doc_snapshot, changes, read_time):
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print(current_time)
    print(f'Number of doc_snapshot: {len(doc_snapshot)}')
    for doc in doc_snapshot:
        if doc.get('position') in ('D1', 'L2', 'KHAC'):
            print(f'{doc.get("position")} - {doc.get(u"is_open")}')
            if doc.get('is_open'):
                #slots[doc.get('position')].lock.blink(on_time = 5, off_time = 1, n=1)
                lock_thread = threading.Thread(target=open_lock, args=(slots[doc.get('position')],))
                lock_thread.start()
            if doc.get('current_capacity') == -1:
                print(slots[doc.get('position')].ultrasonic.distance)
                slots[doc.get('position')].UpdateCapacity()
    event_done.set()


box_ref = db.collection(u'box').document('hbdEcilVp9GmAWUU4a3D')
doc_watch = db.collection(u'slot_info').where('box', '==', box_ref).on_snapshot(on_snapshot)

while True:
    sleep(0.5)
    pass

