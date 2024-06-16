import DevImg from "./Devlmg";
import Image from "next/image";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import {User2, MailIcon, HomeIcon, PhoneCall } from  'lucide-react'



const About = () => {
  return ( 
    <section className="xl:h-[860px] pb-12 xl:py-24">
      <div className="container mx-auto">
        <h2 className="section-title mb-8 xl:mb-16 text-center mx-auto">
          About InterviewMastet
        </h2>
        <div className="flex flex-col xl:flex-row">
          {/* 이미지 */}
          <div className="hidden xl:flex flex-1 relative">
            <DevImg 
              containerStyles='bg-about_shape_dark dark:bg-avout_shape_dark w-[505px] h-[505px] bg-no-repeat relative' 
              imgSrc='/about/main2.png' 
            />
          </div>
          {/* tab */}
          <div className="flex-1">
            <Tabs defaultValue="point1">
              <TabsList>
                <TabsTrigger value='point1'>point1</TabsTrigger>
                <TabsTrigger value='point2'>point2</TabsTrigger>
                <TabsTrigger value='point3'>point3</TabsTrigger>
              </TabsList>
              {/* tabs content */}
              <div className="text-lg mt-12 xl:mt-8">
                {/* point1 */}
                <TabsContent value='point1'>
                  <div className="text-center xl:text-left">
                    <h3 className="h3 mb-4">자소서 기반 맞춤 Service</h3>
                    <p className="subtitle max-w-xl max-auto xl:mx-0">자소서를 기반으로 AI질문 생성 후, 사용자에 맞는 맞춤 면접을 진행합니다.</p>
                  </div>
                </TabsContent>
                <TabsContent value='point2'>
                  <div className="text-center xl:text-left">
                    <h3 className="h3 mb-4">연계 질문 Service</h3>
                    <p className="subtitle max-w-xl max-auto xl:mx-0">연계질문으로 실제 면접과 같은 느낌을 받을 수 있습니다.</p>
                  </div>
                </TabsContent>
                <TabsContent value='point3'>
                  <div className="text-center xl:text-left">
                    <h3 className="h3 mb-4">Simulation Service</h3>
                    <p className="subtitle max-w-xl max-auto xl:mx-0">예상 질문을 바탕으로 영상과 택스트 데이터 제공</p>
                  </div>
                </TabsContent>
              </div>
            </Tabs>
          </div>
        </div>
      </div>
    </section>
  
  );
};

export default About;