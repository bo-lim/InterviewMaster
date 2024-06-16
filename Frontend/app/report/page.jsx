import React from "react"
import DevImg from "../../components/Devlmg";
import { Tabs, TabsList, TabsContent, TabsTrigger } from '@/components/ui/tabs';

const Report = () => {
  return (
    <section className="min-h-screen pt-12 bg-blue-100">
      <div className="container mx-auto">
        <h2 className="section-title mb-8 xl:mb-16 text-center mx-auto"> 
          Report
        </h2>
        <div className="flex flex-col xl:flex-row">
          {/* 이미지 */}
          <div className="hidden xl:flex flex-1 relative">
            <DevImg 
              containerStyles='bg-about_shape_dark dark:bg-avout_shape_dark w-[505px] h-[505px] bg-no-repeat relative' 
              imgSrc='/service/carousel-4.png' 
            />
          </div>
          {/* 텍스트 칸 */}
          <div className="flex-1 p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-2xl font-semibold mb-4">보고서 요약</h3>
            <p className="text-lg mb-4">여기에 보고서 요약 내용을 입력하세요. 예를 들어, 이 보고서에는 면접 결과, 강점 및 개선점, 추천 전략 등이 포함될 수 있습니다.</p>
            <p className="text-lg">보고서는 각 섹션별로 자세한 분석과 평가를 제공하며, 면접자의 성과를 종합적으로 평가합니다.</p>
          </div>
        </div>
      </div>
    </section>
  )
};
export default Report;
