from autofgo import FGOAutoRun, CardAnalyser,Screenshotter


class OrderTest(FGOAutoRun):

    def __init__(self, deviceUrl: str, screenShotter=None):
        super(OrderTest, self).__init__(deviceUrl, screenShotter)
        servantTemplates = {
            "C呆": r"./template/CAL1Order.png",
        }
        strategy = [
            "C呆 Buster -1",         #首选C呆红卡
            "C呆 any -1",            #没有的话选C呆其他卡
            "any any 30",           #没有的话选暴击率30%及以上的卡
            "any Buster -1"         #没有的话选任何其他角色的红卡
                                    #再没有就随便选两张
        ]
        self.orderCardAnalyser = CardAnalyser(servantTemplates, "./template/assistantTag.png", "助战", strategy=strategy, fgoHandler=self.fgoHandler)

    def initElement(self):
        '''
        Returns
        -------
        初始化额外的侦察区域，主要额外增加了选助战头像框的匹配
        '''
        super(OrderTest, self).initElement()

        self.createElement("assistantHeadPic1_1", (88, 307, 323, 476), r".\template\CAL1.png", self.fgoHandler)
        self.createElement("assistantHeadPic1_2", (88, 307, 323, 476), r".\template\CAL2.png", self.fgoHandler)
        self.createElement("assistantHeadPic2_1", (92, 603, 319, 787), r".\template\CAL1.png", self.fgoHandler)
        self.createElement("assistantHeadPic2_2", (92, 603, 319, 787), r".\template\CAL2.png", self.fgoHandler)
        self.createElement("assistantHeadPic3_1", (85, 906, 319, 1056), r".\template\CAL1.png",
                           self.fgoHandler)
        self.createElement("assistantHeadPic3_2", (85, 906, 319, 1056), r".\template\CAL2.png",
                           self.fgoHandler)
        self.createElement("assistantHeadBox1", (85, 307, 1756, 476), None, self.fgoHandler)
        self.createElement("assistantHeadBox2", (85, 603, 1756, 787), None, self.fgoHandler)
        self.createElement("assistantHeadBox3", (85, 906, 1756, 1056), None, self.fgoHandler)

        self.createElement("assistantListRefresh", (1233, 165, 1321, 246), r".\template\assRefresh.png",
                           self.fgoHandler)

    def mainActions(self):
        '''
        Returns
        -------
        战斗流程：先放二号位（女武神）三技能，然后按照策略选指令卡
        '''
        self.targetlessServantSkill(2, 3)
        while self.detectBattleUI(10):
            self.atkAndSelectOrderCard([], self.orderCardAnalyser) #按策略选三张
            #self.atkAndSelectOrderCard([5, 7], self.orderCardAnalyser, mode="mid")  #自选两张，然后把按策略选的一张夹在中间


    def selectAssistant(self):
        '''
        Returns
        -------
        图像识别选再临阶段2和3的C呆，第一页（前三个）没有就刷新
        '''
        while True:
            if self.detect("assistantHeadPic1_1", 2):
                self.tap("assistantHeadBox1")
                break
            elif self.detect("assistantHeadPic1_2", 1, shot=False):
                self.tap("assistantHeadBox1")
                break
            elif self.detect("assistantHeadPic2_1", 1, shot=False):
                self.tap("assistantHeadBox2")
                break
            elif self.detect("assistantHeadPic2_2", 1, shot=False):
                self.tap("assistantHeadBox2")
                break
            elif self.detect("assistantHeadPic3_1", 1, shot=False):
                self.tap("assistantHeadBox3")
                break
            elif self.detect("assistantHeadPic3_2", 1, shot=False):
                self.tap("assistantHeadBox3")
                break
            else:
                self.detect("assistantListRefresh", 10, shot=False, wait=False)
                self.tap("assistantListRefresh")
                self.wait(2, 2.5)
                self.tap("EatAppleBtn")

if __name__ == '__main__':
    deviceUrl = "127.0.0.1:62001"
    fgoAuto = OrderTest(deviceUrl)
    fgoAuto.setConfig(runTimes=2, useApple=True)
    fgoAuto.run()
