from collections import namedtuple
from decimal import Decimal

Price = namedtuple('Price', ['price', 'time'])


def get_lin_avg_price(prices, target):
    # do binary search
    left = 0
    right = len(prices) - 1

    while left <= right:
        mid = left + (right - left) // 2
        if prices[mid].time < target:
            left = mid + 1
        elif prices[mid].time > target:
            right = mid - 1
        else:
            # target found in list
            return prices[mid].price, 0, 0

    # The target is not in the list.
    # Find the closest higher and lower numbers.
    if left == 0 or right == len(prices) - 1:
        return None, None, None
    else:
        p1, t1 = prices[right]
        p2, t2 = prices[left]
        t1 = Decimal(t1.timestamp())
        t2 = Decimal(t2.timestamp())
        t = Decimal(target.timestamp())

        return ((t - t1) * (p2 - p1) / (t2 - t1) + p1, float(t1 - t), float(t2 - t))
