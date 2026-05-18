from opentrons import protocol_api

metadata = {
    "protocolName": "Colored water plate demo",
    "author": "Automation team",
}

requirements = {
    "robotType": "OT-2",
    "apiLevel": "2.16",
}


def run(protocol: protocol_api.ProtocolContext):
    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", 1)
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", 2)
    pipette = protocol.load_instrument("p20_single_gen2", "right")
    pipette.transfer(20, reservoir["A1"], plate["B1"])
