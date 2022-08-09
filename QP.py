from autofgo import FGOAutoRun, Screenshotter, CardAnalyser
from assistantSelectWithSwipe import AssistantSelector

class MySelector(AssistantSelector):

    def initElement(self):
        super(MySelector, self).initElement()
        self.createElement("headPic_1", (100, 165, 1600, 246), r".\template\CAL1.png",
                           self.fgoHandler)
        self.createElement("headPic_2", (100, 165, 1600, 246), r".\template\CAL2.png",
                           self.fgoHandler)
        self.createElement("mysticCodePic", (100, 165, 1600, 246), r".\template\QPMC.png",
                           self.fgoHandler)


    def customJudgement(self, btnPos):
        # 此处的增加值与assistantLoaded的左上偏移量相同
        self.getElement("headPic_1").setPosition((75, btnPos + 240, 320, btnPos + 240 + 240))
        self.getElement("headPic_2").setPosition((75, btnPos + 240, 320, btnPos + 240 + 240))
        self.getElement("mysticCodePic").setPosition((75, btnPos + 240, 320, btnPos + 240 + 240))
        self.getElement("assistantBox").setPosition((100, btnPos + 240, 1600, btnPos + 200 + 240))

        if self.detect("headPic_1", 1, shot=False, wait=False) and self.detect("mysticCodePic", 1, shot=False, wait=False):
            self.tap("assistantBox")
            return True
        if self.detect("headPic_2", 1, shot=False, wait=False) and self.detect("mysticCodePic", 1, shot=False, wait=False):
            self.tap("assistantBox")
            return True
        return False


class QP(FGOAutoRun):

    def __init__(self, deviceurl, screenShotter):
        super(QP, self).__init__(deviceurl, screenShotter)
        #助战选择器设置
        self.assistantSelector = MySelector(deviceurl, screenShotter)
        #选卡策略设置
        servantTemplates = {
            "C呆": r"./template/CAL1Order.png",
        }
        strategy = [
            "小达芬奇 Arts -1",         #首选小达芬奇的蓝卡
            "小达芬奇 Any -1",         #不然试图选小达芬奇的其他卡
            "Any Any -1"            #选择暴击高的卡
        ]
        self.orderCardAnalyser = CardAnalyser(servantTemplates, "./template/assistantTag.png", assistantServantName="助战C呆",
                                              unknownServantName="小达芬奇", strategy=strategy, fgoHandler=self.fgoHandler)



    def mainActions(self):
        # 回合1
        self.detect("ATKBtn", detectFreq=0.3)
        self.targetlessServantSkill(1, 1, wait=(1.2, 1.5))
        self.targetServantSkill(1, 3, 2, wait=(0.7, 1))
        self.targetlessServantSkill(3, 1, wait=(0.7, 1))
        self.targetServantSkill(3, 2, 2, wait=(0.7, 1))
        self.targetServantSkill(3, 3, 2, wait=(0.7, 1))
        self.targetlessServantSkill(2, 1, wait=(0.7, 1))
        self.targetlessServantSkill(2, 3, wait=(0.7, 1))
        self.atkAndSelectOrderCard([2, 0, 0])
        # self.skipCutscenes(wait=(12,13))

        # 回合2
        self.atkAndSelectOrderCard([2, 0, 0])
        self.wait(1, 2)
        # self.skipCutscenes(wait=(12,13))

        # 回合3
        self.atkAndSelectOrderCard([2], self.orderCardAnalyser, mode="prefix")
        self.wait(12, 13)

    def selectAssistant(self):
        self.assistantSelector.selectAssistant()

if __name__ == '__main__':
    deviceUrl = "127.0.0.1:62001"
    screenShotter = Screenshotter(windowSize=(2560, 1440), cropRect=(56, 32, 2465, 1387),windowTitle="夜神模拟器")
    fgoAuto = QP(deviceUrl, screenShotter)
    fgoAuto.setConfig(runTimes=2, useApple=True)
    fgoAuto.run()
