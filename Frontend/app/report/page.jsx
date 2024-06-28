"use client";
import React, { useEffect, useState } from "react";
import DevImg from "../../components/Devlmg";
import { Cookies } from "react-cookie";
import { getReport, post_review } from "../api";
import { Tabs, TabsList, TabsContent, TabsTrigger } from '@/components/ui/tabs';

const Report = () => {
  const [data, setData] = useState(null);
  const [review, setReview] = useState('');
  const [error, setError] = useState(null);  
  const cookies = new Cookies();
  const user_id = cookies.get('user_id'); // 쿠키에서 user_id 가져오기
  const itv_no = cookies.get('itv_no');  // itv_no 값을 정의해야 합니다


  useEffect(() => {
    const fetchData = async () => {
      try {
          
          if (user_id && itv_no) {
            const review_formData = new FormData();
            review_formData.append('itv_no',itv_no);
            const review_response = await post_review(review_formData)
            console.log(review_response)
            setReview(review_response.response)
            const response = await getReport(user_id, itv_no);
            setData(response.itv_info[itv_no]);
            console.log(data);

            // const [question, setQuestion] = useState(data);

          } else {
              console.error("User ID or ITV number is not found");
          }
      } catch (error) {
          setError(error.message);
          console.error("Error fetching data:", error);
        }
      };

      fetchData();
  }, []); // 의존성 배열이 빈 배열이므로 컴포넌트가 마운트될 때만 실행됩니다

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
            <p className="text-lg mb-4">
            {review}

            </p>
            <p className="text-lg">보고서는 각 섹션별로 자세한 분석과 평가를 제공하며, 면접자의 성과를 종합적으로 평가합니다.</p>
          </div>
          <div className="flex-1 p-6 bg-white rounded-lg shadow-md">
            <h3 className="text-2xl font-semibold mb-4">보고서 요약</h3>
            <p className="text-lg mb-4">
            {data && data.qs_info && data.qs_info['01'] && data.qs_info['01'].qs_content}

            </p>
            <p className="text-lg">보고서는 각 섹션별로 자세한 분석과 평가를 제공이보림바보하며, 면접자의 성과를 종합적으로 평가합니다.</p>
          </div>
        </div>
      </div>
    </section>
  )
};
export default Report;
