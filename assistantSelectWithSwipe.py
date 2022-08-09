from autofgo import FGOAutoRun, Screenshotter

import abc
import numpy as np

class AssistantSelector(FGOAutoRun):

    def initElement(self):
        self.createElement("assistantListLoaded", (1633, 240, 1766, 900), r".\template\assLoaded.png", self.fgoHandler)
        self.createElement("assistantListRefresh", (1233, 165, 1321, 246), r".\template\assRefresh2.png",
                           self.fgoHandler)
        self.createElement("assistantBox", (100, 165, 1600, 246), None, self.fgoHandler)

    def selectAssistant(self, swipeTimes=10):
        while True:
            for _ in range(swipeTimes):
                _, res = self.detect("assistantListLoaded", returnDetails=True)
                pos = np.where(res - np.max(res) >= - 0.05)
                diff = np.diff(pos[0])
                diff = np.where(diff > 100)[0] + 1
                btnPos = list(pos[0][diff])
                btnPos.insert(0, pos[0][0])
                for i in range(len(btnPos)):
                    isTap = self.customJudgement(btnPos[i])
                    if isTap:
                        return
                self.fgoHandler.swipe((900, 900),distance=500,duration=(0.5,0.7))
            self.detect("assistantListRefresh", 10, shot=False, wait=False)
            self.tap("assistantListRefresh")
            self.wait(2, 2.5)
            self.tap("EatAppleBtn")
            self.wait(1.5, 2)

    @abc.abstractmethod
    def customJudgement(self, btnPos):
        pass

if __name__ == '__main__':
    deviceUrl = "127.0.0.1:62001"
    screenShotter = Screenshotter(windowSize=(2560, 1440), cropRect=(56, 32, 2465, 1387),windowTitle="夜神模拟器")
    fgoAuto = AssistantSelector(deviceUrl, screenShotter)
    fgoAuto.setConfig(runTimes=1, useApple=False)
    fgoAuto.selectAssistant()