import React, { useState, useEffect } from 'react';
import { MapPin, Clock, Calendar, Trophy, CloudSun, Sparkles, CloudRain, Hourglass, AlertTriangle, ArrowDown, ArrowUp } from 'lucide-react';
import { Player, AppData, MAX_CAPACITY } from './types';
import PlayerForm from './components/PlayerForm';
import PlayerList from './components/PlayerList';

const STORAGE_KEY = 'basketball_data';

export default function App() {
  const [gameDate, setGameDate] = useState<string>(() => {
    // Default to today
    return new Date().toISOString().split('T')[0];
  });
  
  const [players, setPlayers] = useState<Player[]>([]);
  const [editingPlayer, setEditingPlayer] = useState<Player | null>(null);

  // Load data from localStorage
  useEffect(() => {
    const savedData = localStorage.getItem(STORAGE_KEY);
    if (savedData) {
      try {
        const parsed: AppData = JSON.parse(savedData);
        if (parsed.gameDate) setGameDate(parsed.gameDate);
        if (parsed.players) setPlayers(parsed.players);
      } catch (e) {
        console.error("Failed to parse saved data", e);
      }
    }
  }, []);

  // Save data to localStorage
  useEffect(() => {
    const dataToSave: AppData = {
      gameDate,
      players,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(dataToSave));
  }, [gameDate, players]);

  // Handlers
  const handleAddPlayer = (playerData: Omit<Player, 'id' | 'timestamp'>) => {
    const timestamp = Date.now();
    const newPlayers: Player[] = [];

    // 1. Add the main player (yourself)
    // Force count to 1 because we are splitting them
    newPlayers.push({
      ...playerData,
      count: 1, 
      id: crypto.randomUUID(),
      timestamp: timestamp,
    });

    // 2. Add friends as separate entries if count > 1
    if (playerData.count > 1) {
      const friendCount = playerData.count - 1;
      for (let i = 0; i < friendCount; i++) {
        newPlayers.push({
          name: `${playerData.name} (朋友${friendCount > 1 ? i + 1 : ''})`,
          count: 1,
          bringBall: false, // Default friends to not bringing ball to avoid double counting
          occupyCourt: false,
          isMember: false, // Friends are explicitly not members
          id: crypto.randomUUID(),
          timestamp: timestamp + 1 + i, // Slight delay to maintain order
        });
      }
    }

    setPlayers(prev => [...prev, ...newPlayers]);
  };

  const handleUpdatePlayer = (id: string, updatedData: Omit<Player, 'id' | 'timestamp'>) => {
    // When updating, we keep the count logic simple (editing a single entry)
    // If they want to add more friends later, they should add a new entry or we keep it simple here.
    // For this specific requirement, we assume editing applies to that specific row.
    setPlayers(prev => prev.map(p => 
      p.id === id ? { ...p, ...updatedData, count: 1 } : p // Force count 1 to maintain single-entry structure
    ));
    setEditingPlayer(null);
  };

  const handleDeletePlayer = (id: string) => {
    if (window.confirm('確定要刪除這位報名者嗎？')) {
      setPlayers(prev => prev.filter(p => p.id !== id));
      if (editingPlayer?.id === id) {
        setEditingPlayer(null);
      }
    }
  };

  const handleEditClick = (player: Player) => {
    setEditingPlayer(player);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Logic to split Main List vs Waitlist
  const sortedPlayers = [...players].sort((a, b) => a.timestamp - b.timestamp);
  
  const mainList: Player[] = [];
  const waitList: Player[] = [];
  let currentCount = 0;

  sortedPlayers.forEach(player => {
    // Since we split entries, player.count is always 1, but we keep the logic generic just in case
    if (currentCount + player.count <= MAX_CAPACITY) {
      mainList.push(player);
      currentCount += player.count;
    } else {
      waitList.push(player);
    }
  });

  const totalRegistered = players.reduce((sum, p) => sum + p.count, 0);
  const totalWaitlist = waitList.reduce((sum, p) => sum + p.count, 0);

  // Priority Detection Logic
  // Check if there is a MEMBER on the waitlist AND a GUEST (non-member) on the main list
  const memberOnWaitlist = waitList.find(p => p.isMember);
  const guestOnMainlist = mainList.slice().reverse().find(p => !p.isMember); // Find the last guest added (usually distinct friends)
  
  const showPriorityAlert = memberOnWaitlist && guestOnMainlist;

  return (
    <div className="min-h-screen pb-12 bg-sky-50">
      {/* Header / Banner */}
      <div className="bg-gradient-to-r from-sky-400 via-blue-500 to-indigo-500 text-white shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 text-yellow-300 mb-2">
                <CloudSun className="w-6 h-6" />
                <span className="font-bold tracking-wide text-sm bg-white/20 px-2 py-0.5 rounded-full">Sunny Girls Basketball</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-bold flex items-center gap-2">
                晴女在場邊等妳
              </h1>
              <p className="text-sky-100 mt-3 text-base flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-300" />
                祈禱永遠晴天
              </p>
            </div>
            
            <div className="bg-white/10 backdrop-blur-md p-5 rounded-2xl border border-white/20 min-w-[280px] shadow-xl">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Calendar className="w-5 h-5 text-yellow-300" />
                  <div className="flex flex-col">
                    <span className="text-xs text-sky-200">日期 (請點選設定)</span>
                    <input 
                      type="date" 
                      value={gameDate}
                      onChange={(e) => setGameDate(e.target.value)}
                      className="bg-transparent border-b border-white/30 text-white focus:outline-none focus:border-yellow-300 py-0.5 font-medium cursor-pointer"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Clock className="w-5 h-5 text-yellow-300" />
                  <div className="flex flex-col">
                    <span className="text-xs text-sky-200">時間</span>
                    <span className="font-mono font-bold">19:00 開打</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-yellow-300" />
                  <div className="flex flex-col">
                    <span className="text-xs text-sky-200">地點</span>
                    <span className="font-medium">台北市朱崙公園籃球場</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-sky-100 relative overflow-hidden">
            <p className="text-xs text-gray-500 uppercase font-semibold">總報名人數</p>
            <p className="text-2xl font-bold text-gray-800 mt-1">{totalRegistered} <span className="text-sm font-normal text-gray-400">人</span></p>
          </div>

          <div className="bg-white p-4 rounded-xl shadow-sm border border-red-50 relative overflow-hidden">
             <div className="absolute top-0 right-0 p-2 opacity-10">
              <Hourglass className="w-12 h-12 text-red-600" />
            </div>
            <p className="text-xs text-red-500 uppercase font-semibold">目前候補人數</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{totalWaitlist} <span className="text-sm font-normal text-red-300">人</span></p>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-sky-100">
            <p className="text-xs text-gray-500 uppercase font-semibold">幫忙帶球</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-orange-500">
                {players.filter(p => p.bringBall).length}
              </span>
            </div>
          </div>
          
          <div className="bg-white p-4 rounded-xl shadow-sm border border-sky-100">
            <p className="text-xs text-gray-500 uppercase font-semibold">幫忙佔場</p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-2xl font-bold text-green-600">
                {players.filter(p => p.occupyCourt).length}
              </span>
            </div>
          </div>
        </div>

        {/* Main Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Form */}
          <div className="lg:col-span-4 space-y-6">
            <div className="sticky top-6">
              <PlayerForm 
                onSubmit={handleAddPlayer} 
                onUpdate={handleUpdatePlayer}
                onCancelEdit={() => setEditingPlayer(null)}
                editingPlayer={editingPlayer}
              />
              
              <div className="mt-6 bg-white p-5 rounded-xl border border-sky-200 shadow-sm text-sm text-sky-900">
                <h4 className="font-bold flex items-center gap-2 mb-3 text-sky-600">
                  <Trophy className="w-4 h-4" />
                  報名規則說明
                </h4>
                <ul className="space-y-3 text-sky-800/80">
                  <li className="flex gap-2">
                    <span className="text-sky-400"> </span>
                    <span className="flex-1">上限 20 人,超過系統自動轉候補 </span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-sky-400"> </span>
                     <span className="flex-1">每人可帶朋友，系統會自動將朋友列為獨立名單,方便管理 </span>
                  </li>
                  <li className="flex gap-2">
                    <span className="text-sky-400"> </span>
                     <span className="flex-1">若遇額滿，<span className="font-bold text-sky-700 bg-sky-100 px-1 rounded">候補團員 (⭐)</span> 優先取代非團員 </span>
                  </li>
                  <li className="flex gap-2 text-pink-500 font-medium">
                    <span className="text-pink-400"> </span>
                    <span className="flex-1">
                        <CloudRain className="w-4 h-4 inline mr-1" />
                        若遇雨天,當日 17:00 前通知是否取消。
                    </span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Right Column: Lists */}
          <div className="lg:col-span-8 space-y-6">
            <PlayerList 
              title="正選名單 (Main Roster)" 
              players={mainList} 
              onDelete={handleDeletePlayer}
              onEdit={handleEditClick}
              currentCount={currentCount}
              maxCount={MAX_CAPACITY}
            />

            {/* Priority Radar Alert */}
            {showPriorityAlert && (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-xl shadow-sm flex items-start gap-4 animate-pulse">
                 <AlertTriangle className="w-6 h-6 text-yellow-500 shrink-0 mt-0.5" />
                 <div>
                   <h4 className="font-bold text-yellow-800 text-lg">優先權調整建議</h4>
                   <p className="text-yellow-700 text-sm mt-1">
                     偵測到 <strong>團員 {memberOnWaitlist?.name}</strong> 位於候補名單，而正選名單中有 <strong>非團員 (如 {guestOnMainlist?.name})</strong>。
                   </p>
                   <p className="text-yellow-700 text-sm mt-1">
                     建議手動刪除正選名單中的朋友/非團員，讓團員遞補上來。
                   </p>
                   <div className="flex gap-4 mt-2 text-xs font-bold text-yellow-600">
                      <span className="flex items-center gap-1"><ArrowUp className="w-3 h-3"/> 候補團員</span>
                      <span className="flex items-center gap-1"><ArrowDown className="w-3 h-3"/> 正選朋友</span>
                   </div>
                 </div>
              </div>
            )}
            
            {waitList.length > 0 && (
              <PlayerList 
                title="候補名單 (Waitlist)" 
                players={waitList} 
                isWaitlist={true}
                onDelete={handleDeletePlayer}
                onEdit={handleEditClick}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );

}





