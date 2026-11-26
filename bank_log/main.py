import logging

# Logging Configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bank.log", mode="a"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

balance = 10000


# Check Balance
def check_balance():

    logger.debug("Checking account balance")

    print(f"Available Balance: Rs.{balance}")

    logger.info("Balance checked successfully")


# Deposit Amount
def deposit():

    global balance

    amount = float(input("Enter deposit amount: "))

    logger.debug(f"Deposit requested: Rs.{amount}")

    if amount <= 0:
        logger.warning("Invalid deposit amount")
        return

    balance += amount

    logger.info(f"Deposit successful: Rs.{amount}")

    print(f"Available Balance: Rs.{balance}")


# Withdraw Amount
def withdraw():

    global balance

    amount = float(input("Enter withdrawal amount: "))

    logger.debug(f"Withdrawal requested: Rs.{amount}")

    if amount <= 0:
        logger.warning("Invalid withdrawal amount")
        return

    if amount > balance:
        logger.warning("Insufficient balance")
        return

    balance -= amount

    logger.info(f"Withdrawal successful: Rs.{amount}")

    print(f"Available Balance: Rs.{balance}")


# Simulate Database Failure
def database_failure():

    try:
        raise ConnectionError("MySQL connection failed")

    except ConnectionError:
        logger.exception("Database operation failed")


# Simulate Server Failure
def server_failure():

    logger.critical("Banking server is unavailable")

    print("Server failure simulated")


# Display Log File
def view_logs():

    print("\n========== APPLICATION LOGS ==========\n")

    with open("bank.log", "r") as file:
        print(file.read())

    print("=======================================")


# Main Application
logger.info("Banking application started")

while True:

    print("\n========== BANKING APPLICATION ==========")
    print("1. Check Balance")
    print("2. Deposit Amount")
    print("3. Withdraw Amount")
    print("4. Simulate Database Failure")
    print("5. Simulate Server Failure")
    print("6. View All Logs")
    print("7. Exit")
    print("=========================================")

    try:

        choice = int(input("Enter your choice: "))

        logger.debug(f"Customer selected option: {choice}")

        if choice == 1:
            check_balance()

        elif choice == 2:
            deposit()

        elif choice == 3:
            withdraw()

        elif choice == 4:
            database_failure()

        elif choice == 5:
            server_failure()

        elif choice == 6:
            view_logs()

        elif choice == 7:
            logger.info("Banking application stopped")
            print("Thank you for using our banking application")
            break

        else:
            logger.warning("Invalid menu option")

    except ValueError:

        logger.error("Invalid input. Please enter a number")