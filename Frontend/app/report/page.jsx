"use client";
import React, { useEffect, useState } from "react";
import DevImg from "../../components/Devlmg";
import { Cookies } from "react-cookie";
import { getReport, post_review } from "../api";
import { Tabs, TabsList, TabsContent, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardHeader } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import Link from "next/link";


const Report = () => {
//임시 test
const user_id = "ant67410@gmail.com"; // 쿠키에서 user_id 가져오기
const itv_no = "6911b9a58cf54d31bbec08b943a49651_240628_027";

  const [data, setData] = useState(null);
  const [review, setReview] = useState('');
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalTitle, setModalTitle] = useState('');
  const [modalContent, setModalContent] = useState('');
  const cookies = new Cookies();
  // const user_id = cookies.get('user_id'); // 쿠키에서 user_id 가져오기
  // const itv_no = cookies.get('itv_no');  // itv_no 값을 정의해야 합니다

  const showModal = (title, content) => {
    setModalTitle(title);
    setModalContent(content);
    setIsModalOpen(true);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (user_id && itv_no) {
          const review_formData = new FormData();
          review_formData.append('itv_no', itv_no);
          const review_response = await post_review(review_formData);
          console.log(review_response);
          setReview(review_response.response);

          const response = await getReport(user_id, itv_no);
          setData(response.itv_info[itv_no]);
          console.log(response.itv_info[itv_no]);
        } else {
          console.error("User ID or ITV number is not found");
        }
      } catch (error) {
        setError(error.message);
        console.error("Error fetching data:", error);
      }
    };

    fetchData();
  }, [user_id, itv_no]); // user_id와 itv_no가 변경될 때마다 실행됩니다

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!data) {
    return <div>Loading...</div>;
  }

  const questionCards = Object.keys(data.qs_info).map((key) => (
    <Card key={key} className="flex flex-col h-full">
      <CardHeader className="flex-1 flex flex-col justify-between p-6">
        <div>
        <h2 className="text-xl font-bold mb-2">
              Question {key} <br />
              {data.qs_info[key].qs_content}
            </h2>
          <p className="text-muted-foreground">
            
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="mt-4"
          onClick={() =>
            showModal(
              data.qs_info[key].qs_content,
              "Answer",
            )
          }
        >
          View Details
        </Button>
      </CardHeader>
    </Card>
  ));
  

  return (
    <div className="w-full max-w-6xl mx-auto py-8 px-4">
    <h1 className="text-3xl font-bold mb-6">Q&A Report</h1>
    <div className="flex flex-col gap-6">
      <div className="bg-muted px-4 py-2 rounded-md text-muted-foreground font-medium">{review}</div>
      <div className="grid grid-cols-1 gap-6">
        {questionCards}
      </div>
    </div>
    <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{modalTitle}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="prose">{modalContent}</div>
          <div className="flex gap-2">
            <Link href="#" className="flex-1" prefetch={false}>
              <Button variant="outline">Video URL</Button>
            </Link>
            <Link href="#" className="flex-1" prefetch={false}>
              <Button variant="outline">Audio URL</Button>
            </Link>
          </div>
        </div>
        <DialogFooter>
          <div>
            <Button type="button" onClick={() => setIsModalOpen(false)}>Close</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
);
};
export default Report;