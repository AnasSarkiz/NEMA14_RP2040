import type { ChipProps } from 'tscircuit'
const power=(names:string[])=>Object.fromEntries(names.map(n=>[n,{requiresPower:true,mustBeConnected:true}]))
const ground=(names:string[])=>Object.fromEntries(names.map(n=>[n,{requiresGround:true,mustBeConnected:true}]))
export function pinProps(name:string):Pick<ChipProps,'pinAttributes'> {
 const attributes:Record<string,NonNullable<ChipProps['pinAttributes']>[string]>={
  ...({
   U_PD:{...power(['VDD']),...ground(['GND'])},
   U_DRV:{...power(['VDD','VBB1','VBB2']),...ground(['GND','GND18','EP'])},
   U_LDO:{...power(['VIN']),...ground(['GND']),VOUT:{providesPower:true,mustBeConnected:true}},
   U_BUCK:{...power(['VIN']),...ground(['GND']),FB:{mustBeConnected:true},BST:{mustBeConnected:true}},
   U_FLASH:{...power(['VCC']),...ground(['GND','GND18','EP'])},
   U_ESD:{...power(['VBUS']),...ground(['GND'])},
   U_VM_ISO:{...power(['VCC']),...ground(['GND'])},
   Q_DATA:{...ground(['EMITTER'])},
   U_MCU:{...power(['IOVDD1','IOVDD10','IOVDD22','IOVDD33','IOVDD42','IOVDD49','DVDD23','DVDD50','VREG_IN','USB_VDD','ADC_AVDD']),...ground(['GND']),VREG_OUT:{providesPower:true,mustBeConnected:true}},
   J_PD:{VBUS1:{providesPower:true},VBUS2:{providesPower:true},GND1:{providesGround:true},GND2:{providesGround:true}},
   J_DATA:{VBUS1:{providesPower:true},VBUS2:{providesPower:true},GND1:{providesGround:true},GND2:{providesGround:true}},
   J_DEBUG:{VDD:{providesPower:true},GND:{providesGround:true}},
   J_MOTOR:{A_PLUS:{includeInBoardPinout:true},A_MINUS:{includeInBoardPinout:true},B_PLUS:{includeInBoardPinout:true},B_MINUS:{includeInBoardPinout:true}},
   J_BOOT:{BOOT:{includeInBoardPinout:true}},
   Y_MCU:{pin2:{requiresGround:true},pin4:{requiresGround:true}},
  } as Record<string,Record<string,NonNullable<ChipProps['pinAttributes']>[string]>>)[name]??{}
 }
 return {pinAttributes:attributes}
}
