import sys
import time
import signal
import logging
from logging.handlers import RotatingFileHandler

from pyModbusTCP.client import ModbusClient


if __name__ == '__main__':
	# logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    BASIC_FORMAT = "[%(levelname)-s %(asctime)-15s %(name)s %(filename)s:%(lineno)d]: %(message)s"
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)

    file_handler = RotatingFileHandler('fetch_log.log', maxBytes=1024 * 5, backupCount=10)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    def exit(signum, frame):
        logging.info('stop.')
        if c.is_open():
            c.close()
            logger.info('close modbus tcp connection.')
        sys.exit()

    signal.signal(signal.SIGINT, exit)
    signal.signal(signal.SIGTERM, exit)

    # ip & port
    slave_ip = sys.argv[1]
    port = 502
    logger.info(f"slave ip: {slave_ip}, port: {port}")

    c = ModbusClient(host=slave_ip, port=port, timeout=3)
    c.open()

    """
    流程：
    主站写一个 coil，从站读取该值，并将该值赋值给 discrete_input，然后主站再读取该值
    主站写一个 holding_reg，从站读取该值，并赋值给 input_reg，然后主站再读取该值
    """

    coil_value = False
    holding_reg_value = 1
    range_value = 100

    while True:
        if not c.is_open():
            logger.error("not open")
            time.sleep(2)
            continue

        # 写 coils
        c.write_single_coil(1, coil_value)
        logger.debug(f"写 coil，值为 {coil_value}")
        coil_value = not coil_value

        time.sleep(1)

        # 读 discrete_inputs
        inputs = c.read_discrete_inputs(1)
        if inputs is None:
            logger.error("读 discrete_inputs 失败")
            time.sleep(2)
            continue
        logger.debug(f"读 discrete_input，值为 {inputs[0]}")

        # 写 holding_registers
        c.write_single_register(1, holding_reg_value)
        logger.debug(f"写 holding_register，值为 {holding_reg_value}")
        holding_reg_value = (holding_reg_value + 1) % range_value

        time.sleep(1)

        # 读 input_register
        regs = c.read_input_registers(1)
        if regs is None:
            logger.error("读 input_registers 失败")
            time.sleep(2)
            continue
        logger.debug(f"读 input_register，值为 {regs[0]}")

        time.sleep(1)
