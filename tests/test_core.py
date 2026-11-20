import unittest
from fulfillflow.core import Shipment, Status, transition

class ShipmentTests(unittest.TestCase):
    def test_created_to_packed(self):
        self.assertEqual(transition(Shipment("1"), Status.PACKED).status, Status.PACKED)

    def test_created_to_cancelled(self):
        self.assertEqual(transition(Shipment("1"), Status.CANCELLED).status, Status.CANCELLED)

    def test_packed_to_shipped(self):
        self.assertEqual(transition(Shipment("1", Status.PACKED), Status.SHIPPED).status, Status.SHIPPED)

    def test_packed_to_cancelled(self):
        self.assertEqual(transition(Shipment("1", Status.PACKED), Status.CANCELLED).status, Status.CANCELLED)

    def test_shipped_to_delivered(self):
        self.assertEqual(transition(Shipment("1", Status.SHIPPED), Status.DELIVERED).status, Status.DELIVERED)

    def test_shipped_to_return(self):
        self.assertEqual(transition(Shipment("1", Status.SHIPPED), Status.RETURN_TO_SENDER).status, Status.RETURN_TO_SENDER)

    def test_shipped_to_cancelled_is_forbidden(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.SHIPPED), Status.CANCELLED)

    def test_delivered_is_terminal(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.DELIVERED), Status.CANCELLED)

    def test_cancelled_is_terminal(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.CANCELLED), Status.PACKED)

    def test_return_is_terminal(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.RETURN_TO_SENDER), Status.DELIVERED)

    def test_cannot_skip_packing(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1"), Status.SHIPPED)

    def test_cannot_cancel_twice(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.CANCELLED), Status.CANCELLED)

    def test_cannot_deliver_from_packed(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.PACKED), Status.DELIVERED)

    def test_cannot_return_before_ship(self):
        with self.assertRaises(ValueError):
            transition(Shipment("1", Status.PACKED), Status.RETURN_TO_SENDER)

if __name__ == "__main__":
    unittest.main()
