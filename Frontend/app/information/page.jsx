'use client';
import React, { useEffect, useState } from "react";
import "../globals.css";
import DevImg from '../../components/Devlmg';
import { Button } from "../../components/ui/button";
import { useSearchParams, useRouter  } from 'next/navigation';
import { Cookies } from 'react-cookie';
import axios from "axios";



const Information = () => {
  const cookies = new Cookies();
  const [start, setStart] = useState(0);
  const [disabled, setDisabled] = useState(true);
  const router = useRouter();
  
  const handleButton = (event) => {
    router.push("/interview");
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.post(`${process.env.NEXT_PUBLIC_CAHT_POST_API}/coverletter/`, 
          {
            coverletter_url: cookies.get('coverletter_url'),
            position: cookies.get('position')
          });

        console.log(response);
        setDisabled(false);
        //console.log(response.data.response);
        console.log(response.data.thread_id);

        // 쿠키에 데이터 저장
        cookies.set('simul_info', response.data.response);
        cookies.set('simul_ques', response.data.question);
        cookies.set('thread_id', response.data.thread_id);
      } catch (error) {
        console.log(error);
      }
    };
    if(start==0){
      setStart(1);
      fetchData();
    }
  }, []);

  return (
    <section className="min-h-screen pt-12">
      <div className="container mx-auto">
        <h1 className="section-title mb-8 xl:mb-8 text-center mx-auto"> 
          Information 
        </h1>
        <h3 className="h2 mb-16 text-center custom-font">
          면접이 곧 시작됩니다.
        </h3>
        <div>
          <p className="font-bold text-xl mb-4">아래의 안내사항을 잘 읽고 참여해주세요!</p>
        </div>
        <div className="bg-blue-100 p-4 rounded-md text-left mb-16"> {/* 여기서 mb-16은 아래 간격을 16으로 설정 */}
          <p className="h4 font-bold text-lg mb-4">모의 면접 도중, 새로고침은 불가합니다! 이 점 꼭 유의 해주세요.</p>
          <p className="font-bold text-lg mb-4">1. 면접 질문이 끝나면 5초의 시간이 주어집니다. 5초 후에 답해주세요!</p>
          <p className="font-bold text-lg mb-4">2. 첫 번째 질문에는 자소서를 기반으로 질문이 제공되며, 그 후는 본인이 대답한 내용에 대한 추가 질문이 주어집니다.</p>
          <p className="font-bold text-lg mb-4">3. 질문에 대답하지 못할 경우, 자소서 기반의 새로운 주제의 질문이 주어집니다.</p>
          <p className="font-bold text-lg">4. 답변을 완료하면 END 버튼을 꼭 눌러주세요!</p>
        </div>
        <div className="bg-blue-50 p-8 rounded-md text-left mb-10 flex items-center"> {/* 추가적인 파란색 박스 */}
          <div className="flex-1">
            <p className="font-bold text-xl mb-4">개인 정보 동의(필수)</p>
            
            {/* 체크 박스 세로 정렬 */}
            <div className="flex flex-col space-y-2">
              <div className="flex items-center">
                <input type="checkbox" id="checkbox1" className="mr-2" />
                <label htmlFor="checkbox1" className="text-sm">
                  개인 정보 동의
                </label>
              </div>
              <div className="flex items-center">
                <input type="checkbox" id="checkbox2" className="mr-2" />
                <label htmlFor="checkbox2" className="text-sm">
                  카메라 녹화 허용
                </label>
              </div>
              <div className="flex items-center">
                <input type="checkbox" id="checkbox3" className="mr-2" />
                <label htmlFor="checkbox3" className="text-sm">
                  비디오 녹화 허용
                </label>
              </div>
            </div>
          </div>
          <div className="hidden xl:flex relative">
            <DevImg 
              containerStyles='w-[300px] h-[300px] bg-no-repeat relative bg-bottom'
              imgSrc='/information/agreeimg.png'/>
          </div>
        </div>
        {/* 버튼 추가 */}
        <div className="flex justify-center">
       
            <Button onClick={handleButton} disabled={disabled} className='gap-x-2 py-3 px-6 text-lg'>
              Start
            </Button>
         
        </div>
      </div>
    </section>
  );
};

export default Information;
