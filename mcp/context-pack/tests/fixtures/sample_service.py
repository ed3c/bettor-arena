class Ledger:
    def __init__(self) -> None:
        self.balance = 0

    async def settle(self, amount: int, hook_name: str) -> int:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.balance += amount
        hook = getattr(self, hook_name)
        hook(amount)
        return self.balance
