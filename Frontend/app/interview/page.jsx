import React from "react";

const Interview = () => {
  return (
    <div className="container mx-auto">
      <div className="my-8">
        <h2 className="text-3xl font-semibold mb-4">면접 질문</h2>
        <div className="bg-gray-100 p-4 mb-8">
          <p className="text-lg">여기에 면접 질문 내용이 들어갑니다.</p>
          <p className="text-lg">예시 질문: 자기소개, 경험, 역량 등</p>
        </div>
      </div>
      <div className="relative">
        <div className="bg-black text-white rounded-lg overflow-hidden shadow-xl aspect-w-16 aspect-h-9 max-w-5xl mx-auto">
          {/* 비디오 재생을 위한 <video> 태그 */}
          <video
            className="w-full h-auto"
            src="/yotubevideo/interviewmaster.mp4"
            autoPlay
            loop
            muted
            controls
          >
          </video>
        </div>
      </div>
      <div className="text-center mt-8">
        <button className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-400">
          Next
        </button>
      </div>
    </div>
  );
};

export default Interview;
